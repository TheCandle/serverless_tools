import os
import time
import numpy as np
import math
import onnxruntime
import torch
# import utils
# from structure import no_dop_operator_features, no_dop_operators_exec, no_dop_operators_mem, dop_operators_exec, dop_operators_mem, parallel_op

from config.structure_config import (
    no_dop_operators_exec,
    no_dop_operators_mem,
    dop_operators_exec,
    dop_operators_mem,
    parallel_op,
    dop_operator_features,
    no_dop_operator_features,
)

class ONNXModelManager:
    # --- 修改 __init__ 方法 ---
    def __init__(self, no_dop_model_dir="output/models/operator_non_dop_aware",
                       dop_model_dir="output/models/operator_dop_aware"):
        """
        初始化 ONNX 模型管理器。

        Args:
            no_dop_model_dir (str): 非 DOP 感知模型所在的目录路径 (相对于项目根目录)。
            dop_model_dir (str): DOP 感知模型所在的目录路径 (相对于项目根目录)。
        """
        # 将传入的相对路径转换为绝对路径 (假设脚本是从项目根目录运行的)
        # 或者，调用者(scripts脚本)可以直接传入绝对路径
        self.no_dop_model_dir = os.path.abspath(no_dop_model_dir)
        self.dop_model_dir = os.path.abspath(dop_model_dir)
        print(f"ONNX Manager: Loading non-DOP models from: {self.no_dop_model_dir}")
        print(f"ONNX Manager: Loading DOP models from: {self.dop_model_dir}")

        self.exec_sessions = {}
        self.mem_sessions = {}
        self.load_models() # load_models 方法保持不变
    # --- 结束修改 ---

    def has_exec_model(self, operator_type):
        return operator_type in self.exec_sessions

    def has_mem_model(self, operator_type):
        return operator_type in self.mem_sessions

    def _get_feature_schema(self, operator_type, target='exec'):
        schema = dop_operator_features.get(operator_type)
        if schema is None:
            schema = no_dop_operator_features.get(operator_type)
        if not schema:
            return None
        return schema.get(target)

    def _align_feature_array(self, operator_type, feature_data, expected_dim, target='exec'):
        arr = np.array(feature_data).reshape(1, -1).astype(np.float32)
        got_dim = arr.shape[1]

        if expected_dim is None or got_dim == expected_dim:
            return arr

        feature_schema = self._get_feature_schema(operator_type, target=target)
        if feature_schema and len(feature_schema) == expected_dim and got_dim < expected_dim:
            padded = np.zeros((1, expected_dim), dtype=np.float32)
            padded[:, :got_dim] = arr
            missing_features = feature_schema[got_dim:]
            print(
                f"⚠️ ONNX {target} feature dim auto-aligned for '{operator_type}': "
                f"got={got_dim}, expected={expected_dim}, padded_zeros={expected_dim - got_dim}, "
                f"missing_tail_features={missing_features}"
            )
            return padded

        mismatch_msg = (
            f"ONNX {target} input dim mismatch for operator '{operator_type}': "
            f"got {got_dim}, expected {expected_dim}."
        )
        if feature_schema:
            mismatch_msg += (
                f" Configured feature count={len(feature_schema)}."
                f" First configured features={feature_schema[:min(10, len(feature_schema))]}"
            )
        mismatch_msg += " This usually means the exported model and inference feature config are from different versions."
        raise ValueError(mismatch_msg)

    def load_models(self):
        dop_operators = set()
        # 遍历模型目录,加载所有 ONNX 模型
        for operator_type in os.listdir(self.dop_model_dir):
            operator_path = os.path.join(self.dop_model_dir, operator_type)
            if os.path.isdir(operator_path):
                dop_operators.add(operator_type)
                # 将 operator_type 中的空格替换为下划线
                operator_name = operator_type.replace(' ', '_')
                if operator_type in dop_operators_exec:
                    # 加载执行时间模型
                    exec_model_path = os.path.join(operator_path, f"exec_{operator_name}.onnx")
                    if os.path.exists(exec_model_path):
                        self.exec_sessions[operator_type] = onnxruntime.InferenceSession(exec_model_path)
                if operator_type in dop_operators_mem:
                    # 加载内存模型
                    mem_model_path = os.path.join(operator_path, f"mem_{operator_name}.onnx")
                    if os.path.exists(mem_model_path):
                        self.mem_sessions[operator_type] = onnxruntime.InferenceSession(mem_model_path)
        for operator_type in os.listdir(self.no_dop_model_dir):
            operator_path = os.path.join(self.no_dop_model_dir, operator_type)
            if os.path.isdir(operator_path):
                # 将 operator_type 中的空格替换为下划线
                operator_name = operator_type.replace(' ', '_')
                if operator_type in no_dop_operators_exec:
                    # 加载执行时间模型
                    exec_model_path = os.path.join(operator_path, f"exec_{operator_name}.onnx")
                    if os.path.exists(exec_model_path):
                        self.exec_sessions[operator_type] = onnxruntime.InferenceSession(exec_model_path)
                if operator_type in no_dop_operators_mem:
                    # 加载内存模型
                    mem_model_path = os.path.join(operator_path, f"mem_{operator_name}.onnx")
                    if os.path.exists(mem_model_path):
                        self.mem_sessions[operator_type] = onnxruntime.InferenceSession(mem_model_path)

    def infer_exec(self, operator_type, feature_data):
        # 将 operator_type 中的空格替换为下划线以匹配模型文件名
        if operator_type not in self.exec_sessions:
            raise UserWarning(f"No execution model found for operator type: {operator_type}")

        session = self.exec_sessions[operator_type]
        # 在运行前做显式维度检查；当配置可判定且仅缺少尾部特征时自动补零对齐
        input_meta = session.get_inputs()[0]
        input_name = input_meta.name
        input_shape = input_meta.shape  # 例如 [None, 31]
        expected_dim = None
        if isinstance(input_shape, (list, tuple)) and len(input_shape) > 1 and isinstance(input_shape[1], int):
            expected_dim = input_shape[1]

        feature_array = self._align_feature_array(
            operator_type=operator_type,
            feature_data=feature_data,
            expected_dim=expected_dim,
            target='exec'
        )

        inputs = {input_name: feature_array}
        exec_pred = session.run(None, inputs)
        exec_pred[0][0]
        return exec_pred[0][0]

    def infer_mem(self, operator_type, feature_data):
        # 将 operator_type 中的空格替换为下划线以匹配模型文件名
        if operator_type not in self.mem_sessions:
            raise ValueError(f"No memory model found for operator type: {operator_type}")

        session = self.mem_sessions[operator_type]
        input_meta = session.get_inputs()[0]
        input_name = input_meta.name
        input_shape = input_meta.shape
        expected_dim = None
        if isinstance(input_shape, (list, tuple)) and len(input_shape) > 1 and isinstance(input_shape[1], int):
            expected_dim = input_shape[1]

        feature_array = self._align_feature_array(
            operator_type=operator_type,
            feature_data=feature_data,
            expected_dim=expected_dim,
            target='mem'
        )

        inputs = {input_name: feature_array}
        mem_pred = session.run(None, inputs)
        return mem_pred[0][0]