from math import sqrt

# 导入系统配置
from .main_config import USE_HASH_TABLE_SIZE_FEATURE, DEFAULT_DOP, THREAD_COST, THREAD_MEM

# Create lowercase aliases for compatibility with existing code
default_dop = DEFAULT_DOP
thread_cost = THREAD_COST
thread_mem = THREAD_MEM

# 1. 定义列类型到开销的映射
column_type_cost_dict = {
    'INT': 4,              # INT 类型开销 4 字节
    'BIGINT': 8,           # BIGINT 类型开销 8 字节
    'CHAR': lambda s: 4 + s * 2,   # CHAR(n) 类型开销为 n 字节
    'VARCHAR': lambda s: 4 + s * 2, # VARCHAR(n) 类型开销为 n 字节
    'DECIMAL': lambda p, s: 4 + 4 + (p + s),  # DECIMAL(p, s) 假设开销为 (p + s) / 2 字节
    'DATE': 8              # DATE 类型开销 8 字节
}

tpcds_non_parallel = {1,2,3,9,23,24,30,32,33,42,54,56,57,59,60,63,64,77,80,81,92}

# 2. 预定义的表结构及列类型
table_structure = {
    'REGION': [
        ('R_REGIONKEY', 'INT'),
        ('R_NAME', 'CHAR(25)'),
        ('R_COMMENT', 'VARCHAR(152)')
    ],
    'NATION': [
        ('N_NATIONKEY', 'INT'),
        ('N_NAME', 'CHAR(25)'),
        ('N_REGIONKEY', 'INT'),
        ('N_COMMENT', 'VARCHAR(152)')
    ],
    'SUPPLIER': [
        ('S_SUPPKEY', 'BIGINT'),
        ('S_NAME', 'CHAR(25)'),
        ('S_ADDRESS', 'VARCHAR(40)'),
        ('S_NATIONKEY', 'INT'),
        ('S_PHONE', 'CHAR(15)'),
        ('S_ACCTBAL', 'DECIMAL(15,2)'),
        ('S_COMMENT', 'VARCHAR(101)')
    ],
    'CUSTOMER': [
        ('C_CUSTKEY', 'BIGINT'),
        ('C_NAME', 'VARCHAR(25)'),
        ('C_ADDRESS', 'VARCHAR(40)'),
        ('C_NATIONKEY', 'INT'),
        ('C_PHONE', 'CHAR(15)'),
        ('C_ACCTBAL', 'DECIMAL(15,2)'),
        ('C_MKTSEGMENT', 'CHAR(10)'),
        ('C_COMMENT', 'VARCHAR(117)')
    ],
    'PART': [
        ('P_PARTKEY', 'BIGINT'),
        ('P_NAME', 'VARCHAR(100)'),
        ('P_MFGR', 'CHAR(100)'),
        ('P_BRAND', 'CHAR(20)'),
        ('P_TYPE', 'VARCHAR(100)'),
        ('P_SIZE', 'BIGINT'),
        ('P_CONTAINER', 'CHAR(10)'),
        ('P_RETAILPRICE', 'DECIMAL(15,2)'),
        ('P_COMMENT', 'VARCHAR(23)')
    ],
    'PARTSUPP': [
        ('PS_PARTKEY', 'BIGINT'),
        ('PS_SUPPKEY', 'BIGINT'),
        ('PS_AVAILQTY', 'BIGINT'),
        ('PS_SUPPLYCOST', 'DECIMAL(15,2)'),
        ('PS_COMMENT', 'VARCHAR(199)')
    ],
    'ORDERS': [
        ('O_ORDERKEY', 'BIGINT'),
        ('O_CUSTKEY', 'BIGINT'),
        ('O_ORDERSTATUS', 'CHAR(1)'),
        ('O_TOTALPRICE', 'DECIMAL(15,2)'),
        ('O_ORDERDATE', 'DATE'),
        ('O_ORDERPRIORITY', 'CHAR(15)'),
        ('O_CLERK', 'CHAR(15)'),
        ('O_SHIPPRIORITY', 'BIGINT'),
        ('O_COMMENT', 'VARCHAR(79)')
    ],
    'LINEITEM': [
        ('L_ORDERKEY', 'BIGINT'),
        ('L_PARTKEY', 'BIGINT'),
        ('L_SUPPKEY', 'BIGINT'),
        ('L_LINENUMBER', 'BIGINT'),
        ('L_QUANTITY', 'DECIMAL(15,2)'),
        ('L_EXTENDEDPRICE', 'DECIMAL(15,2)'),
        ('L_DISCOUNT', 'DECIMAL(15,2)'),
        ('L_TAX', 'DECIMAL(15,2)'),
        ('L_RETURNFLAG', 'CHAR(1)'),
        ('L_LINESTATUS', 'CHAR(1)'),
        ('L_SHIPDATE', 'DATE'),
        ('L_COMMITDATE', 'DATE'),
        ('L_RECEIPTDATE', 'DATE'),
        ('L_SHIPINSTRUCT', 'CHAR(25)'),
        ('L_SHIPMODE', 'CHAR(10)'),
        ('L_COMMENT', 'VARCHAR(44)')
    ]
}

# OPERATORS_WITHOUT_FEATURES = {
#     'Row Adapter', 'Vector Limit', 'Vector Sort Aggregate',
#     'Vector Subquery Scan', 'Sort', 'Nested Loop',
#     # 根据你的实际情况添加或删除
# }

# 假设已知的 jointype 和 table_names 类型
jointypes = ['none', 'Inner', 'Right', 'Left', 'Full', 'Semi', 'Anti', 'Right Semi', 'Right Anti', 'Left Anti Full', 'Right Anti Full']
table_names = ['none', 'region', 'nation', 'supplier', 'customer', 'part', 'partsupp', 'orders', 'lineitem']
operator_type =[
    'CStore Index Scan',
        'Vector Nest Loop',
        'Vector Merge Join',
        'Aggregate',
        'Hash',
        'Vector WindowAgg',
        'Append',
        'Index Only Scan',
        'Hash Join',
        'CStore Scan',
        'Vector Materialize',
        'Vector Aggregate',
        'Vector Sort',
        'Vector Hash Aggregate',
        'Vector Sonic Hash Aggregate',
        'Vector Hash Join',
        'Vector Sonic Hash Join',
        'Vector Streaming LOCAL GATHER',
        'Vector Streaming LOCAL REDISTRIBUTE', 
        'Vector Streaming BROADCAST',
        'Vector SetOp',
        'Vector Append',
        'Row Adapter',
        'Vector Limit',
        'Streaming(type: BROADCAST dop: 64/1)',
        'Streaming(type: LOCAL REDISTRIBUTE dop: 64/64)', 
        'Streaming(type: LOCAL GATHER dop: 1/64)',
        'Vector Subquery Scan',
        'CTE Scan',


        # presto算子
         'ScanFilterProject',
        'Aggregate',
        'AssignUniqueId',
        'CrossJoin',
        'EnforceSingleRow',
        'FilterProject',
        'InnerJoin',
        'LeftJoin',
        'LocalExchange',
        'LocalMerge',
        'PartialSort',
        'Project',
        'RemoteSource',
        'ScanFilter',
        'ScanProject',
        'SemiJoin',
        'TableScan',
        ]
# 创建编码字典
jointype_encoding = {jointype: idx for idx, jointype in enumerate(jointypes)}
table_names_encoding = {table_name: idx for idx, table_name in enumerate(table_names)}
operator_encoding = {operator_type: idx for idx, operator_type in enumerate(operator_type)}

# Materialized (pipeline breaker) operator rules.
# Keep this centralized so switching engine/operator names only needs config changes.
materialized_operator_types = {
    # openGauss / legacy
    'Vector Materialize',
    'Vector Aggregate',
    'Vector Hash Aggregate',
    'Vector Sonic Hash Aggregate',
    'Vector Sort',
    'Vector Sort Aggregate',
    'Vector Streaming LOCAL GATHER',
    'Vector Streaming LOCAL REDISTRIBUTE',
    'Vector Streaming BROADCAST',
    'Streaming(type: BROADCAST dop: 64/1)',
    'Streaming(type: LOCAL REDISTRIBUTE dop: 64/64)',
    'Streaming(type: LOCAL GATHER dop: 1/64)',
    'Hash',
    'Hash Join',
    'Aggregate',
    # Presto
    'LocalExchange',
    'LocalMerge',
    'PartialSort',
    'RemoteSource',
    'EnforceSingleRow',
}

# Keyword fallback for engines/operators not explicitly listed above.
materialized_operator_keywords = (
    'materialize',
    'aggregate',
    'sort',
    # 'hash',
    # 'exchange',
    'join',
    # 'remote',
    'merge',
    'enforcesinglerow',
)

parallel_op = [
        'CStore Scan',
        'Vector Materialize',
        'Vector Aggregate',
        'Vector Sort',
        'Vector Hash Aggregate',
        'Vector Sonic Hash Aggregate',
        'Vector Hash Join',
        'Vector Sonic Hash Join',
        'Vector Streaming LOCAL GATHER',
        'Vector Streaming LOCAL REDISTRIBUTE', 
        'Vector Streaming BROADCAST',
        'Streaming(type: BROADCAST dop: 64/1)',
        'Streaming(type: LOCAL REDISTRIBUTE dop: 64/64)', 
        'Streaming(type: LOCAL GATHER dop: 1/64)',
        'Vector Result',
        'Vector WindowAgg',
        'Vector SetOp',
        'Vector Append',
        'Vector Limit',
        'Vector Subquery Scan',
        'Vector Sort Aggregate',
        'Aggregate',
        'Hash',
        'Hash Join',
        'Row Adapter',


        # presto
        'ScanFilterProject',
        'Aggregate',
        'AssignUniqueId',
        'CrossJoin',
        'EnforceSingleRow',
        'FilterProject',
        'InnerJoin',
        'LeftJoin',
        'LocalExchange',
        'LocalMerge',
        'PartialSort',
        'Project',
        'RemoteSource',
        'ScanFilter',
        'ScanProject',
        'SemiJoin',
        'TableScan',
]

# 训练时一个个那该列表中算子的特征进行训练
operator_lists = [
        'CStore Index Scan',
        'Vector Nest Loop',
        'Vector Merge Join',
        'Aggregate',
        'Hash',
        'Vector WindowAgg',
        'Append',
        'Index Only Scan',
        'Hash Join',
        'CStore Scan',
        'Vector Materialize',
        'Vector Aggregate',
        'Vector Sort',
        'Vector Hash Aggregate',
        'Vector Sonic Hash Aggregate',
        'Vector Hash Join',
        'Vector Sonic Hash Join',
        'Vector Streaming LOCAL GATHER',
        'Vector Streaming LOCAL REDISTRIBUTE', 
        'Vector Streaming BROADCAST',
        'Vector SetOp',
        'Vector Append',

        # presto算子
        'ScanFilterProject',
        'Aggregate',
        'AssignUniqueId',
        'CrossJoin',
        'EnforceSingleRow',
        'FilterProject',
        'InnerJoin',
        'LeftJoin',
        'LocalExchange',
        'LocalMerge',
        'PartialSort',
        'Project',
        'RemoteSource',
        'ScanFilter',
        'ScanProject',
        'SemiJoin',
        'TableScan',
]
no_dop_operators_exec = [
        'CStore Index Scan',
        'Vector Nest Loop',
        'Vector WindowAgg',
        'Index Only Scan',
        'Vector Merge Join',
]

dop_operators_exec = [
        # 'CStore Scan',
        # 'Vector Materialize',
        # 'Vector Aggregate',
        # 'Vector Sort',
        # 'Vector Hash Aggregate',
        # 'Vector Sonic Hash Aggregate',
        # 'Vector Hash Join',
        # 'Vector Sonic Hash Join',
        # 'Vector Streaming LOCAL GATHER',
        # 'Vector Streaming LOCAL REDISTRIBUTE', 
        # 'Vector Streaming BROADCAST',
        # 'Vector SetOp',
        # 'Vector Append',
        # 'Aggregate',
        # 'Hash',
        # 'Append',
        # 'Hash Join',


        # Presto
        'ScanFilterProject',
        'Aggregate',
        'AssignUniqueId',
        'CrossJoin',
        'EnforceSingleRow',
        'FilterProject',
        'InnerJoin',
        'LeftJoin',
        'LocalExchange',
        'LocalMerge',
        'PartialSort',
        'Project',
        'RemoteSource',
        'ScanFilter',
        'ScanProject',
        'SemiJoin',
        'TableScan',
        
]

no_dop_operators_mem = [
    'Vector Materialize',
    'Vector Aggregate',
    'Vector Sort',
    'Vector Hash Aggregate',
    'Vector Sonic Hash Aggregate',
    'Vector Hash Join',
    'Vector Sonic Hash Join',
    'Vector WindowAgg',
    'Aggregate',
    'Hash',
]

dop_operators_mem = [
        # 'Vector Materialize',
        # 'Vector Aggregate',
        # 'Vector Sort',
        # 'Vector Hash Aggregate',
        # 'Vector Sonic Hash Aggregate',
        # 'Vector Hash Join',
        # 'Vector Sonic Hash Join',
        # 'Vector SetOp',

        'ScanFilterProject',
        'Aggregate',
        'AssignUniqueId',
        'CrossJoin',
        'EnforceSingleRow',
        'FilterProject',
        'InnerJoin',
        'LeftJoin',
        'LocalExchange',
        'LocalMerge',
        'PartialSort',
        'Project',
        'RemoteSource',
        'ScanFilter',
        'ScanProject',
        'SemiJoin',
        'TableScan',
]


no_dop_operator_features = {
    'CStore Index Scan': {
        'exec': ['l_input_rows', 'actual_rows', 'width', 'index_cost', 'predicate_cost'],
        'mem': ['l_input_rows', 'actual_rows', 'width', 'query_dop']
    },
    'CTE Scan': {
        'exec': ['l_input_rows', 'actual_rows', 'width', 'predicate_cost'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    # Add mappings for other operators here
    'Vector Nest Loop': {
        'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'query_dop'],
        'mem': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'query_dop']
    },
    'Vector Merge Join': {
        'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype'],
        'mem': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width','jointype']
    },
    'Vector WindowAgg': {
        'exec': ['l_input_rows', 'actual_rows', 'width'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    'Index Only Scan': {
        'exec': ['l_input_rows', 'actual_rows', 'width', 'index_cost', 'predicate_cost'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    'Vector Aggregate': {
        'exec': ['l_input_rows', 'actual_rows', 'width', 'agg_width'],
        'mem': ['l_input_rows', 'actual_rows', 'width', 'agg_width']
    },
    'Vector Sort': {
        'exec': ['l_input_rows', 'actual_rows', 'width'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    'Vector Materialize': {
        'exec': ['l_input_rows', 'actual_rows', 'width'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    'Vector Hash Aggregate': {
        'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'hash_table_size', 'disk_ratio'],
        'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'hash_table_size', 'disk_ratio']
    },
    # 'Vector Hash Aggregate': {
    #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    #     'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # },
    'Vector Sonic Hash Aggregate': {
        'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'hash_table_size', 'disk_ratio'],
        'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'hash_table_size', 'disk_ratio']
    },
    # 'Vector Sonic Hash Aggregate': {
    #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    #     'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # },
    'Vector Hash Join': {
        'exec': ['l_input_rows', 'r_input_rows',  'width', 'jointype', 'predicate_cost', 'hash_table_size'],
        'mem': ['r_input_rows', 'width', 'hash_table_size']
    },
    'Vector Sonic Hash Join': {
        'exec': ['l_input_rows', 'r_input_rows',  'width', 'jointype', 'predicate_cost','hash_table_size'],
        'mem': ['r_input_rows', 'width', 'hash_table_size']
    },
    # 'Vector Hash Join': {
    #     'exec': ['l_input_rows', 'r_input_rows', 'width', 'jointype', 'predicate_cost'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    #     'mem': ['r_input_rows', 'width'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # },
    # 'Vector Sonic Hash Join': {
    #     'exec': ['l_input_rows', 'r_input_rows', 'width', 'jointype', 'predicate_cost'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    #     'mem': ['r_input_rows', 'width'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # },
    'Vector SetOp': {
        'exec': ['l_input_rows',  'actual_rows', 'width'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    'Aggregate': {
        'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width'],
        'mem': ['l_input_rows', 'width', 'agg_col', 'agg_width']
    },
    'Vector Sort Aggregate': {
        'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width'],
        'mem': ['l_input_rows', 'width', 'agg_col', 'agg_width']
    },
    'Hash Join': {
        'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost', 'hash_table_size'],
        'mem': ['r_input_rows', 'width', 'jointype', 'hash_table_size']
    },
    # 'Hash Join': {
    #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    #     'mem': ['r_input_rows', 'width', 'jointype'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # },
    'Hash': {
        'exec': ['l_input_rows', 'actual_rows', 'width'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    'Append': {
        'exec': ['l_input_rows', 'actual_rows', 'width'],
        'mem': ['l_input_rows', 'actual_rows', 'width']
    },
    # Add more operators and their corresponding feature sets here as needed
}

# 这里定义每个算子训练时用到的特征
dop_operator_features = {
    # 'CStore Scan': {
    #     'exec': ['l_input_rows', 'actual_rows', 'width', 'predicate_cost'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector Aggregate': {
    #     'exec': ['l_input_rows', 'actual_rows', 'width', 'agg_width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width', 'agg_width']
    # },
    # 'Vector Sort': {
    #     'exec': ['l_input_rows', 'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector Materialize': {
    #     'exec': ['l_input_rows', 'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector Hash Aggregate': {
    #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'],
    #     'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'hash_table_size', 'disk_ratio']
    # },
    # # 'Vector Hash Aggregate': {
    # #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'],
    # #     'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # # },
    # 'Vector Sonic Hash Aggregate': {
    #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'],
    #     'mem': ['actual_rows', 'width', 'agg_col', 'agg_width', 'hash_table_size', 'disk_ratio']
    # },
    # # 'Vector Sonic Hash Aggregate': {
    # #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width', 'disk_ratio'],
    # #     'mem': ['actual_rows', 'width', 'agg_col', 'agg_width',  'disk_ratio'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # # },
    # 'Vector Hash Join': {
    #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost', 'hash_table_size'],
    #     'mem': ['r_input_rows', 'width', 'hash_table_size']
    # },
    # # 'Vector Hash Join': {
    # #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    # #     'mem': ['r_input_rows', 'width'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # # },
    # 'Vector Sonic Hash Join': {
    #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost','hash_table_size'],
    #     'mem': ['r_input_rows', 'width', 'hash_table_size']
    # },
    # # 'Vector Sonic Hash Join': {
    # #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    # #     'mem': ['r_input_rows', 'width'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # # },
    # 'Vector Streaming LOCAL GATHER': {
    #     'exec': ['l_input_rows',  'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector Streaming LOCAL REDISTRIBUTE': {
    #     'exec': ['l_input_rows',  'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector Streaming BROADCAST': {
    #     'exec': ['l_input_rows',  'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector SetOp': {
    #     'exec': ['l_input_rows',  'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Vector Append': {
    #     'exec': ['l_input_rows',  'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Aggregate': {
    #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width'],
    #     'mem': ['l_input_rows', 'width', 'agg_col', 'agg_width']
    # },
    # 'Vector Sort Aggregate': {
    #     'exec': ['l_input_rows', 'width', 'agg_col', 'agg_width'],
    #     'mem': ['l_input_rows', 'width', 'agg_col', 'agg_width']
    # },
    # 'Hash Join': {
    #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost', 'hash_table_size'],
    #     'mem': ['r_input_rows', 'width', 'jointype', 'hash_table_size']
    # },
    # # 'Hash Join': {
    # #     'exec': ['l_input_rows', 'r_input_rows', 'actual_rows', 'width', 'jointype', 'predicate_cost'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else []),
    # #     'mem': ['r_input_rows', 'jointype', 'width'] + (['hash_table_size'] if USE_HASH_TABLE_SIZE_FEATURE else [])
    # # },
    # 'Hash': {
    #     'exec': ['l_input_rows', 'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },
    # 'Append': {
    #     'exec': ['l_input_rows', 'actual_rows', 'width'],
    #     'mem': ['l_input_rows', 'actual_rows', 'width']
    # },

    # Add more operators and their corresponding feature sets here as needed
    'ScanFilterProject': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'Aggregate': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'AssignUniqueId': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'CrossJoin': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'EnforceSingleRow': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'FilterProject': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'InnerJoin': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'LeftJoin': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'LocalExchange': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'LocalMerge': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'PartialSort': {
        'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'Project': {
         'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ] 
    },
        'RemoteSource': {
         'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ] 
    },
        'ScanFilter': {
       'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ] 
    },
        'ScanProject': {
         'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ]  
    },
        'SemiJoin': {
         'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ] 
    },
        'TableScan': {
         'exec': ['l_input_rows', 'r_input_rows' ],
        'mem': ['l_input_rows', 'r_input_rows' ] 
    },

}

# Presto native operators that may not exist in openGauss datasets.
# Keep them as independent operators instead of forcing semantic remapping.
PRESTO_NATIVE_OPERATORS = [
    'MergeOperator',
    'ExplainAnalyzeOperator',
    'TaskOutputOperator',
    'ExchangeOperator',
    'OrderBy',
    'LocalMerge',
    'CallbackSink',
    'PartitionedOutput',
    'LocalExchangeSourceOperator',
    'HashBuilderOperator',
    'LookupJoinOperator',
    'LocalExchangeSinkOperator',
    'Aggregation',
    'PartialAggregation',
    'NestedLoopJoinBuild',
    'NestedLoopJoinProbe',
]

def _extend_unique(target_list, values):
    for value in values:
        if value not in target_list:
            target_list.append(value)

# Ensure these operators can enter train/infer loops.
_extend_unique(operator_lists, PRESTO_NATIVE_OPERATORS)
_extend_unique(operator_type, PRESTO_NATIVE_OPERATORS)
_extend_unique(parallel_op, PRESTO_NATIVE_OPERATORS)
_extend_unique(dop_operators_exec, PRESTO_NATIVE_OPERATORS)
_extend_unique(dop_operators_mem, PRESTO_NATIVE_OPERATORS)
operator_encoding = {op_name: idx for idx, op_name in enumerate(operator_type)}

# Conservative materialization tags for common pipeline breakers.
for _op in [
    'ExchangeOperator',
    'LocalExchangeSourceOperator',
    'LocalExchangeSinkOperator',
    'PartitionedOutput',
    'OrderBy',
    'Aggregation',
    'PartialAggregation',
    'HashBuilderOperator',
    'LocalMerge',
]:
    materialized_operator_types.add(_op)

# Default lightweight feature template for unseen Presto-native operators.
for _op in PRESTO_NATIVE_OPERATORS:
    if _op not in dop_operator_features:
        dop_operator_features[_op] = {
            'exec': ['l_input_rows', 'r_input_rows'],
            'mem': ['l_input_rows', 'r_input_rows'],
        }

# 全局特征列表 - 分别收集exec和mem特征
all_exec_features = set()
all_mem_features = set()

# 收集所有dop_operator_features中的特征
for op_type, features in dop_operator_features.items():
    all_exec_features.update(features.get('exec', []))
    all_mem_features.update(features.get('mem', []))

# 收集所有no_dop_operator_features中的特征
for op_type, features in no_dop_operator_features.items():
    all_exec_features.update(features.get('exec', []))
    all_mem_features.update(features.get('mem', []))

# 创建全局特征列表（分别用于exec和mem模型）
global_exec_feature_list = sorted(list(all_exec_features))
global_mem_feature_list = sorted(list(all_mem_features))

# 这里定义每个算子训练是的轮数。
dop_train_epochs = {
    'CStore Scan': {
        'exec': 150,
        'mem': 20
    },
    'Vector Aggregate': {
        'exec': 100,
        'mem': 100
    },
    'Vector Sort': {
        'exec': 100,
        'mem': 100
    },
    'Vector Materialize': {
        'exec': 100,
        'mem': 100
    },
    'Vector Hash Aggregate': {
        'exec': 100,
        'mem': 100
    },
    'Vector Sonic Hash Aggregate': {
        'exec': 200,
        'mem': 100
    },
    'Vector Hash Join': {
        'exec': 200,
        'mem': 100
    },
    'Vector Sonic Hash Join': {
        'exec': 100,
        'mem': 100
    },
    'Vector Streaming LOCAL GATHER': {
        'exec': 100,
        'mem': 100
    },
    'Vector Streaming LOCAL REDISTRIBUTE': {
        'exec': 120,
        'mem': 100
    },
    'Vector Streaming BROADCAST': {
        'exec': 100,
        'mem': 100
    },
    'Vector SetOp': {
        'exec': 100,
        'mem': 100
    },
    'Vector Append': {
        'exec': 100,
        'mem': 100
    },
    'Aggregate': {
        'exec': 100,
        'mem': 50
    },
    'Append': {
        'exec': 100,
        'mem': 50
    },
    'Hash Join': {
        'exec': 100,
        'mem': 50
    },
    'Hash': {
        'exec': 100,
        'mem': 50
    },
    'Vector Append': {
        'exec': 100,
        'mem': 50
    },
    'Vector Sort Aggregate': {
        'exec': 100,
        'mem': 50
    },

    # Add more operators and their corresponding feature sets here as needed
    'ScanFilterProject': {
        'exec': 100,
        'mem': 50
     },
    'Aggregate': {
        'exec': 100,
        'mem': 50
     },
    'AssignUniqueId': {
        'exec': 100,
        'mem': 50
    },
    'CrossJoin': {
        'exec': 100,
        'mem': 50
    },
    'EnforceSingleRow': {
        'exec': 100,
        'mem': 50
    },
    'FilterProject': {
        'exec': 100,
        'mem': 50
    },
    'InnerJoin': {
        'exec': 100,
        'mem': 50
    },
    'LeftJoin': {
        'exec': 100,
        'mem': 50
    },
    'LocalExchange': {
        'exec': 100,
        'mem': 50
    },
    'LocalMerge': {
        'exec': 100,
        'mem': 50
    },
    'PartialSort': {
        'exec': 100,
        'mem': 50
    },
    'Project': {
        'exec': 100,
        'mem': 50
    },
    'RemoteSource': {
        'exec': 100,
        'mem': 50
    },
    'ScanFilter': {
        'exec': 100,
        'mem': 50
    },
    'ScanProject': {
        'exec': 100,
        'mem': 50
    },
    'SemiJoin': {
        'exec': 100,
        'mem': 50
    },
    'TableScan': {
        'exec': 100,
        'mem': 50
    }
}

# Ensure newly introduced operators always have training epoch config.
for _op in PRESTO_NATIVE_OPERATORS:
    if _op not in dop_train_epochs:
        dop_train_epochs[_op] = {
            'exec': 100,
            'mem': 50,
        }