import pandas as pd
import quandl
import pickle

quandl.ApiConfig.api_key = open("quandl_key.env").read()

tickers_df = quandl.get_table('SHARADAR/TICKERS',paginate=True)


def help():
	print(
		"The stock analysis library includes the following functionality:\n" + 
		"Watchlist class: a watchlist that stores stocks with their priorities\n"+ 
		"Watchlist functionality: push, front, remove, pop, view\n"+
		"get_metrics(ticker, metrics_to_display): display a metric for a given stock\n"+
		"quick_view(ticker): view various important metrics pertaining to a stock\n"+
		"daily_view(ticker,num_days,display=[]): view daily changes in multiples or other metrics\n"+
		"competitor_view(ticker,specced_comps,category,filter_revenue): view analysis on competitors\n"+
		"quick_valuation(ticker,ann_ebitda_growth,future_ebitda_multiple,num_yrs,share_change,cash_change,debt_change)\n"+
		"quick_screener_fg(revenue_growth, num_yrs): screen for fast growers at low multiples\n"+
		"quick_screener_bs(): screen for stocks with a strong balance sheet"
		)

class Watchlist:
    def __init__(self):
        f = open('watchlist.pickle','rb')
        self.stocks = pickle.load(f)
        self.stocks.sort(key=lambda x:x[0])
    def push(self,ticker,priority=1):
        self.stocks.append( (priority,ticker) )
        self.stocks.sort(key=lambda x:x[0])
    def front(self):
        return self.stocks[0][1]
    def remove(self,ticker):
        for x in self.stocks:
            if ticker == x[1]:
                self.stocks.remove(x)
                return True
        return False
    def pop(self):
        el_1 = self.stocks[0]
        self.stocks.remove(el_1)
    def view(self):
        return self.stocks
    def __del__(self):
        f = open('watchlist.pickle','wb')
        pickle.dump(self.stocks,f)

def get_metrics(t,metrics_to_display):
    metrics_to_display.insert(0,'calendardate')
    SF1_df = quandl.get_table('SHARADAR/SF1',ticker=t,dimension='MRY')[::-1]
    return SF1_df[metrics_to_display]

#quick view of any stock with key metrics
def quick_view(t):
    metrics_to_display = [
        'calendardate',
        #tier 1
        'evebitda', 'pe', 'ps','eps','revenue','roic', 'eps_growth','revenue_growth','fcf_growth',
        #tier 2
        'net_debt_ps', 'cash_ps','debt_ps', 'pct_change_cash', 'tangible_book_value_ps', 'ptb', 
        'pct_change_debt', 'currentratio', 'debt_to_equity', 
        #tier 3
        'fcf', 'price','pfcf','grossmargin','netmargin','ebitdamargin', 'intangibles_ps'
    ]
    #get ticker, return dataframe of relevant metrics
    
    SF1_df = quandl.get_table('SHARADAR/SF1',ticker=t,dimension='MRY')[::-1]
    cashneq = SF1_df['cashnequsd']
    totaldebt = SF1_df['debtusd']
    num_shares = SF1_df['shareswa']
    tangible_assets = SF1_df['tangibles']
    total_liabilities = SF1_df['liabilities']
    marketcap = SF1_df['marketcap']
    intangibles = SF1_df['intangibles']    
    
    #balance sheet metrics
       
    SF1_df['debt_ps'] = (totaldebt) / num_shares
    #(cash - total debt) per share
    SF1_df['net_debt_ps'] = (cashneq - totaldebt) / num_shares
    #cash per share
    SF1_df['cash_ps'] = cashneq / num_shares
    #change in cash y/y
    SF1_df['pct_change_cash'] = cashneq.pct_change()
    #tangible book value per share
    SF1_df['tangible_book_value_ps'] = (tangible_assets - total_liabilities) / num_shares
    #price to tangible_book_value
    SF1_df['ptb'] = marketcap / (tangible_assets - total_liabilities)
    #goodwill and intangibles per share
    SF1_df['intangibles_ps'] = intangibles / num_shares
    #change in debt y/y
    SF1_df['pct_change_debt'] = totaldebt.pct_change()
    #debt to equity
    SF1_df['debt_to_equity'] = total_liabilities / (SF1_df['assets'] - total_liabilities)
    #multiples
    SF1_df['pfcf'] = marketcap / SF1_df['fcf']
    
    #eps growth
    SF1_df['eps_growth'] = SF1_df['eps'].pct_change()
    #revenue growth
    SF1_df['revenue_growth'] = SF1_df['revenue'].pct_change()
    #FCF growth
    SF1_df['fcf_growth'] = SF1_df['fcf'].pct_change()
    
    return SF1_df[metrics_to_display]
    
#daily stock view
def daily_view(t,num_days=7,display = ['date','evebitda','marketcap','pe','pb','ps']):
    SF1_df = quandl.get_table('SHARADAR/DAILY',ticker=t)[:num_days][::-1]
    return SF1_df[display]
    
#competitor stock view
def competitor_view(t,specced_comps=[],category='industry',filter_revenue=False):
    #tickers_df = quandl.get_table('SHARADAR/TICKERS',paginate=True)
    ticker_info = quandl.get_table('SHARADAR/TICKERS',ticker=t)
    ticker_cat = ticker_info[category].values[0]
    #ticker_scale = ticker_info[filter_competitor].values[0]
    
    competitors = []
    if specced_comps == []:
        competitors = list(set(tickers_df[tickers_df[category]==ticker_cat]['ticker'].values))
    else:
        competitors = specced_comps
    
    to_df = []
    competitors.append(t)
    for c in competitors:
        try:
	        temp_dict = {}
	        daily_multiples = quandl.get_table('SHARADAR/DAILY',ticker=c)[::-1].loc[0]
	        temp_dict['ticker'] = c
	        temp_dict['evebitda'] = daily_multiples['evebitda']
	        temp_dict['pe'] = daily_multiples['pe']
	        temp_dict['ps'] = daily_multiples['ps']
	        temp_dict['pb'] = daily_multiples['pb']
	        
	        SF1_df = quandl.get_table('SHARADAR/SF1',ticker=c,dimension='MRY')[::-1]
	        temp_dict['1yr_eps_growth'] = SF1_df['eps'].pct_change()[0]
	        temp_dict['1yr_revenue_growth'] = SF1_df['revenue'].pct_change()[0]
	        temp_dict['1yr_fcf_growth'] = SF1_df['fcf'].pct_change()[0]
	        
	        temp_dict['5yr_avg_eps_growth'] = SF1_df['eps'].pct_change()[:5].mean()
	        temp_dict['5yr_avg_revenue_growth'] = SF1_df['revenue'].pct_change()[:5].mean()
	        temp_dict['5yr_avg_fcf_growth'] = SF1_df['fcf'].pct_change()[:5].mean()
	        
	        temp_dict['grossmargin'] = SF1_df['grossmargin'][0]
	        temp_dict['netmargin'] = SF1_df['netmargin'][0]
	        temp_dict['ebitdamargin'] = SF1_df['ebitdamargin'][0]
	        
	        temp_dict['eps'] = SF1_df['eps'][0]
	        temp_dict['revenue'] = SF1_df['revenue'][0]
	        to_df.append(temp_dict)
        except:
	        continue
    ret_df = pd.DataFrame(to_df)
    
    avg_row = {}
    avg_row['ticker'] = 'AVG'
    for k in temp_dict.keys():
        if k == "ticker":
            continue
        else:
            avg_row[k] = ret_df[k].mean()
            
    ret_df = ret_df.append(avg_row, ignore_index=True)
    return ret_df

#valuation
def quick_valuation(t,ann_ebitda_growth,future_ebitda_multiple,num_yrs=5,share_change=0,cash_change=0,debt_change=0):
    SF1_df = quandl.get_table('SHARADAR/SF1',ticker=t,dimension='MRY')[::-1]
    
    curr_ebitda = SF1_df['ebitda'][0]
    curr_cashneq = SF1_df['cashnequsd'][0]
    curr_debt = SF1_df['debtusd'][0]
    curr_num_shares = SF1_df['shareswa'][0]
    
    future_cash = curr_cashneq + cash_change
    future_debt = curr_debt + debt_change
    future_num_shares = curr_num_shares + share_change
    
    future_ebitda = curr_ebitda * ((1+ann_ebitda_growth)**num_yrs)
    future_EV = future_ebitda*future_ebitda_multiple
    
    future_price = (future_EV + future_cash - future_debt) / future_num_shares
    print('Current Price:',SF1_df['price'][0])
    print(num_yrs,'Yr Price Target:', future_price)

#screener -- fast growers
def quick_screener_fg(revenue_growth=0.15,num_yrs=5,output=False):
    #tickers_df = quandl.get_table('SHARADAR/TICKERS',paginate=True)
    SF1_df = quandl.get_table('SHARADAR/SF1',paginate=True)
    screened_stocks = []
    count = 0
    for t in tickers_df['ticker'].unique():
        if count % 100 == 0:
             print("Tickers at",count,":",screened_stocks)
        #high revenue growth
        try: 
	        SF1_df_t = quandl.get_table('SHARADAR/SF1',ticker=t,dimension='MRY')[::-1]
	        SF1_df_t['revenue_growth'] = SF1_df_t['revenue'].pct_change()
	        mean_rev_growth = SF1_df_t['revenue_growth'][:num_yrs].mean()
	        if mean_rev_growth > revenue_growth:
	            
	            #low relative valuation
	            ticker_industry = tickers_df[tickers_df['ticker']==t]['industry'].values
	            if ticker_industry != []:
		            competitors = tickers_df[tickers_df['industry']==ticker_industry[0]]['ticker'].values
		            
		            if competitors != []:
				            mean_EBITDA_multiple = SF1_df[SF1_df['ticker'].isin(competitors)]['evebitda'].mean()
				            mean_PS_multiple = SF1_df[SF1_df['ticker'].isin(competitors)]['ps'].mean()
				            
				            ticker_evebitda = SF1_df_t['evebitda'][0]
				            ticker_ps = SF1_df_t['ps'][0]
			            
				            if output:
				            	print("Ticker:",t)
				            	print("\tEBITDA Multiple:",ticker_evebitda)
				            	print("\tPS:",ticker_ps)
				            	print("\tRevenue Growth:",mean_rev_growth)
				            if (ticker_evebitda < 0) or (mean_EBITDA_multiple < 0): 
				                if ticker_ps < mean_PS_multiple:
				                    screened_stocks.append(t)
				                    print('BUY:',t)
				            else:
				                if ticker_evebitda < mean_EBITDA_multiple:
				                    screened_stocks.append(t)
				                    print('BUY:',t)
				            count+=1
        except:
	        print('Unknown error. Please manually analyze.')

    return screened_stocks 

#screener -- strong balance sheet
def quick_screener_bs(output=False):
    screened_stocks = []
    #tickers_df = quandl.get_table('SHARADAR/TICKERS',paginate=True)
    for t in tickers_df['ticker'].unique():
    	if output:
    		print('Ticker',t)
    	try:
	        SF1_df = quandl.get_table('SHARADAR/SF1',ticker=t,dimension='MRY')[::-1]
	        cashneq = SF1_df['cashnequsd']
	        totaldebt = SF1_df['debtusd']
	        num_shares = SF1_df['shareswa']
	        tangible_assets = SF1_df['tangibles']
	        total_liabilities = SF1_df['liabilities']
	        marketcap = SF1_df['marketcap']
	        
	        SF1_df = quandl.get_table('SHARADAR/SF1',ticker=t,dimension='MRY')[::-1]
	        #(cash - total debt) per share
	        SF1_df['net_debt_ps'] = (cashneq - totaldebt) / num_shares
	        #cash per share
	        SF1_df['cash_ps'] = cashneq / num_shares
	        #change in cash y/y
	        SF1_df['pct_change_cash'] = cashneq.pct_change()
	        #tangible book value per share
	        SF1_df['ptb'] = marketcap / (tangible_assets - total_liabilities)
	        #change in debt y/y
	        SF1_df['pct_change_debt'] = totaldebt.pct_change()
	        
	        high_cash = (SF1_df['net_debt_ps'][0] > 0)
	        low_ptb = (SF1_df['ptb'][0] < 1)
	        five_yr_decreasing_debt = (SF1_df['pct_change_debt'][:5].mean() < 0)
	        five_yr_increasing_cash = (SF1_df['pct_change_cash'][:5].mean() > .07)
	        if output:
	        	print('\tHigh Cash:',high_cash)
	        	print('\tLow PTB:',low_ptb)
	        	print('\t5 YR Decreasing Debt:',five_yr_decreasing_debt)
	        	print('\t5 YR Increasing Cash:',five_yr_increasing_cash)
	        if (high_cash + low_ptb + five_yr_decreasing_debt + five_yr_increasing_cash) >= 3:
	            screened_stocks.append(t)
    	except:
	        print('Unknown error. Please analyze manually.')
	        continue
    return screened_stocks