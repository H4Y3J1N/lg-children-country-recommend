# import sys
# sys.path.append("../../src")

import numpy as np
import pandas as pd

from utils import ndcg_calculator

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules




def Data_load(path:str):
    test_answer_week = pd.read_parquet(path + "test_answer_week.parquet")
    test_answer_month = pd.read_parquet(path + "test_answer_month.parquet")

    df_train_week = pd.read_parquet(path + "train_week.parquet")
    df_train_month = pd.read_parquet(path + "train_month.parquet")

    sample_sumbission_week = pd.read_parquet(path + "sample_sumbission_week.parquet")
    sample_sumbission_month = pd.read_parquet(path + "sample_sumbission_month.parquet")

    # apriori 순서 반영
    df_train_week.sort_values(by='log_dt', inplace=True)
    df_train_month.sort_values(by='log_dt', inplace=True)

    return test_answer_week, test_answer_month, df_train_week, df_train_month, sample_sumbission_week, sample_sumbission_month




def Most_popular(df_train_week, df_train_month, n):
    MP_list_week = list(df_train_week.album_id.value_counts().head(n).index)
    MP_list_month = list(df_train_month.album_id.value_counts().head(n).index)

    return MP_list_week, MP_list_month




def Apriori_encoder(df_train:pd.DataFrame())->pd.DataFrame():
    # each user's album_id to list
    transactions = [transaction[1]['album_id'].tolist() for transaction in \
                         list(df_train.groupby('profile_id'))]
    
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    
    orders_1hot = pd.DataFrame(te_ary, columns=te.columns_)
    '''
    output -> DataFrame(True&False)
    '''
    return orders_1hot




def Apriori_train(orders_1hot:pd.DataFrame(), min_support_num:int, min_threshold_num:int)->pd.DataFrame():

    is_ap = apriori(orders_1hot, min_support=min_support_num, use_colnames=True)
    
    # matrix의 default가 confidence
    rules_confidence_item = association_rules(is_ap, min_threshold= min_threshold_num)

    #lift 기준으로 sort
    rules_confidence_item = rules_confidence_item.sort_values(['lift'], ascending = False)
    return rules_confidence_item




def Apriori_pred(df_train:pd.DataFrame(), rules_confidence_item:pd.DataFrame())->pd:
    unique_user_transaction_list = df_train.groupby('profile_id')['album_id'].unique().reset_index()

    # user transaction 목록을 가져와 lift 순으로 consequents 담기
    rules_confidence_list = []
    for album_list in unique_user_transaction_list['album_id']:
        user_consequents_list = []
        for idx, antecedents in enumerate(rules_confidence_item['antecedents']):
            # issubset -> antecedents 하위집합이면 True
            if antecedents.issubset(album_list):
                user_consequents_list += rules_confidence_item['consequents'][idx]
        # 순서 유지 중복 제거
        rules_confidence_list.append(list(dict.fromkeys(user_consequents_list)))
    # apriori pred 담기    
    unique_user_transaction_list['album_id'] = rules_confidence_list
    
    return unique_user_transaction_list




def Apriori_week_month(MP_list, df_train, rules_confidence_item, \
                        sample_sumbission, n):
    # Apriori pred@25
    apriori_pred = Apriori_pred(df_train, rules_confidence_item)
    apriori_sumbission = sample_sumbission.copy().drop(columns='album_id')
    apriori_sumbission = apriori_sumbission.merge(apriori_pred, on='profile_id')
    apriori_sumbission['album_id'] = apriori_sumbission['album_id'].apply(lambda x: x[:n])
    # Apriori + MP pred@25
    apriori_mp_sumbission = apriori_sumbission.copy()
    apriori_mp_sumbission['album_id'] = apriori_sumbission['album_id'].apply(lambda x: (x + MP_list)[:n])

    return apriori_sumbission, apriori_mp_sumbission




def Excute_apriori(path='../data/', n=25, min_support_num=0.1, min_threshold_num=0.8):

    test_answer_week, test_answer_month, df_train_week, df_train_month, sample_sumbission_week, sample_sumbission_month = Data_load(path)

    MP_list_week, MP_list_month = Most_popular(df_train_week, df_train_month)

    orders_1hot_week = Apriori_encoder(df_train_week)
    orders_1hot_month = Apriori_encoder(df_train_month)

    rules_confidence_item_week = Apriori_train(orders_1hot_week, min_support_num=min_support_num , min_threshold_num=min_threshold_num)
    rules_confidence_item_month = Apriori_train(orders_1hot_month, min_support_num=min_support_num , min_threshold_num=min_threshold_num)

    apriori_sumbission_week, apriori_mp_sumbission_week  = Apriori_week_month(MP_list_week, df_train_week, rules_confidence_item_week, sample_sumbission_week, n)
    apriori_sumbission_month, apriori_mp_sumbission_month  = Apriori_week_month(MP_list_month, df_train_month, rules_confidence_item_month, sample_sumbission_month, n)
                        
    apriori_week_ndcg = ndcg_calculator(test_answer_week, apriori_sumbission_week, n)
    apriori_mp_week_ndcg = ndcg_calculator(test_answer_week, apriori_mp_sumbission_week, n)

    apriori_month_ndcg = ndcg_calculator(test_answer_month, apriori_sumbission_month, n)
    apriori_mp_month_ndcg = ndcg_calculator(test_answer_month, apriori_mp_sumbission_month, n)

    print("Week performance")
    print(f"nDCG(apriori): {apriori_week_ndcg:.4f}")
    print(f"nDCG(apriori + mp): {apriori_mp_week_ndcg:.4f} \n")

    print("Month performance")
    print(f"nDCG(apriori): {apriori_month_ndcg:.4f}")
    print(f"nDCG(apriori + mp): {apriori_mp_month_ndcg:.4f}")

    return rules_confidence_item_week, rules_confidence_item_month


if __name__ =="__main__":
    Excute_apriori()