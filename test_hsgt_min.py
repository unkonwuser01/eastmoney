import akshare as ak                                                                                              
import pandas as pd                                                                                               
                                                                                                          
try:                                                                                                              
    print("Fetching stock_hsgt_fund_min_em for '北向资金'...")                                                    
    # This usually returns the minute-level flow for the current day                                              
    #df1 = ak.stock_hsgt_fund_min_em(symbol="北向资金")  
    df = ak.stock_bid_ask_em(symbol="920046")                                                           
                                                                                                                  
    if df is not None and not df.empty:                                                                           
        print("Columns:", df.columns.tolist())                                                                    
        print("First 10 rows:")                                                                                    
        print(df.head(100))                                                                                         
        print("Last 10 rows:")                                                                                     
        print(df.tail(100))                                                                                         
                                                                                                                  
        # Determine the latest net inflow                                                                         
        # Usually looking for something like '时间', '沪股通', '深股通', '北向资金'                               
        # Or maybe it has '净流入'                                                                                
                                                                                                                  
        # Calculate latest accumulated flow                                                                       
        last_row = df.iloc[-1]                                                                                    
        print("\nLast row data:", last_row.to_dict())                                                             
                                                                                                                  
    else:                                                                                                         
        print("DataFrame is empty or None")                                                                       
                                                                                                                  
except Exception as e:                                                                                            
    print(f"Error: {e}")