import numpy as np
import pandas as pd
from datetime import timedelta
import math




####### History 

def history_feature_engineering(df):
    
    ####### Short trailer & Continuous play - categorical
    cat_features = ['short_trailer','continuous_play']
    for i in enumerate (cat_features) :
        col = i[1]
        df[col] = df[col].astype('category')
        
    ####### album_viewcount - Frequency    
    album_viewcount_df = df.groupby("album_id").size()/len(df)
    df.loc[:, "album_viewcount_freq"] = df["album_id"].map(album_viewcount_df)
    df[["album_id","short_trailer","continuous_play","album_viewcount_freq"]]
    return df




def watch_feature_engineering(watch):
    watch['continuous_play'] = watch['continuous_play'].astype('category')
    watch_feature = watch[['profile_id','album_id','continuous_play','total_time']]
    return watch_feature




def paid_feature_engineering(df,buy):
    history_pay = df[["album_id","payment"]].copy()
    paid_album = list(set(buy["profile_id"].unique().tolist() + history_pay.dropna().drop_duplicates().album_id.unique().tolist()))
    label = [1]*len(paid_album)
    paid_label_df = pd.DataFrame(zip(paid_album, label)).rename(columns=({0:"album_id",1:"paid_label"}))
    paid_df = pd.merge(df,paid_label_df,on="album_id",how="left")
    paid_df["paid_label"] = paid_df["paid_label"].fillna(0).astype(int).astype("category")
    paid_feature = paid_df[["profile_id","album_id","paid_label"]]
    paid_feature = paid_feature[paid_feature["paid_label"]==1].drop_duplicates()
    return paid_feature




def searched_feature_engineering(df,search):
    search_album = search["album_id"].unique().tolist()
    label = [1]*len(search_album)
    searched_label_df = pd.DataFrame(zip(search_album, label)).rename(columns=({0:"album_id",1:"searched_label"}))
    searched_df = pd.merge(df,searched_label_df,on="album_id",how="left")
    searched_df["searched_label"] = searched_df["searched_label"].fillna(0).astype(int).astype("category")
    return searched_df




def meta_feature_engineering(meta):
    
    ####### sub_title & genre_large & genre_mid - categorical
    cat_features = ['sub_title','genre_large','genre_mid','country']
    for i in enumerate (cat_features) :
        col = i[1]
        meta[col] = meta[col].astype('category')

    return meta




def profile_feature_engineering(profile):
    #######  sex / age / pr_interest_keyword_cd_1 / ch_interest_keyword_cd_1 - categorical
    cat_features = ['sex','age','pr_interest_keyword_cd_1','ch_interest_keyword_cd_1']
    for i in enumerate(cat_features) :
        col = i[1]
        profile[col] = profile[col].astype('category')
        
    ####### age binning    
    bins = [0,2,5,7,10,13] 
    group_names = ['영아','유아','초등준비','초등저학년','초등고학년'] #한솔교육 제품군 참조
    profile['age_bin'] = pd.cut(profile['age'],bins,labels=group_names)
    profile['age_bin'] = profile['age_bin'].astype('category')    
    
    return profile