import pandas as pd
from transaction_classifier import TransactionClassifier

# 构造测试数据
sample = {
    '交易对方': '测试商家',
    '商品说明': '测试商品',
    '金额': 12.34,
    '收/支': '支出',
    '交易分类': '购物',
}
df = pd.DataFrame([sample])

# 新建分类器
classifier = TransactionClassifier()

# 添加自定义分类
classifier.add_user_classification(df.iloc[0], '自定义-测试分类', persist=True)

# 再次分类，应该命中自定义分类
classified = classifier.classify_transaction(df.iloc[0])
print('分类结果:', classified)
assert classified == '自定义-测试分类', '自定义分类未生效!'

# 测试批量分类
result_df = classifier.classify_all_transactions(df)
print('批量分类结果:', result_df['分类'].tolist())
assert result_df['分类'].iloc[0] == '自定义-测试分类', '批量自定义分类未生效!'

print('user_rules.json自定义分类功能测试通过！')

