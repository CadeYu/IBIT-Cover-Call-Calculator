import yfinance as yf
import pandas as pd
import numpy as np
import mibian
from datetime import datetime, timedelta

def get_current_price(ticker):
    """Fetches the current market price of the ticker using history for speed."""
    stock = yf.Ticker(ticker)
    # .info is slow. Use fast_info or history
    try:
        # Try fast_info first (newer yfinance versions)
        return stock.fast_info['last_price']
    except:
        # Fallback to history
        hist = stock.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
        return 0.0

def get_risk_free_rate():
    """Fetches the 13-week Treasury Bill rate as a proxy for risk-free rate."""
    try:
        # ^IRX is 13 week treasury bill yield index
        irx = yf.Ticker("^IRX")
        # Divide by 100 because index is e.g. 4.5 for 4.5%
        return irx.info.get('regularMarketPrice') / 100
    except:
        return 0.045 # Fallback to 4.5%

def get_option_dates(ticker):
    """Fetches available expiration dates."""
    stock = yf.Ticker(ticker)
    return stock.options

def get_option_chain(ticker, date):
    """Fetches the call option chain for a specific date."""
    stock = yf.Ticker(ticker)
    chain = stock.option_chain(date)
    return chain.calls

def calculate_metrics(calls_df, current_price, expiration_date, risk_free_rate=0.045):
    """
    Calculates Annualized Yield and Greeks for the option chain.
    """
    results = []
    
    # Calculate days to expiration
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    today = datetime.now()
    days_to_exp = (exp_date - today).days
    
    # Avoid division by zero
    if days_to_exp <= 0:
        days_to_exp = 1
        
    years_to_exp = days_to_exp / 365.0
    
    for index, row in calls_df.iterrows():
        strike = row['strike']
        bid = row['bid']
        ask = row['ask']
        last_price = row.get('lastPrice', 0.0)
        
        # Premium Calculation Logic
        # 1. Best case: Mid price
        if bid > 0 and ask > 0:
            premium = (bid + ask) / 2
        # 2. Fallback: If only one side exists (rare but possible)
        elif bid > 0:
            premium = bid
        elif ask > 0:
            premium = ask
        # 3. Last Resort: Use last traded price (lastPrice)
        # Note: This might be stale, but better than 0 for visualization
        elif last_price > 0:
            premium = last_price
        else:
            premium = 0.0
        
        # 1. Annualized Yield Calculation
        # Yield = (Premium / Strike) * (365 / DTE)
        # Note: Some calculate yield on Current Price, but for "Covered Call" thinking about collateral:
        # If assigned, you sell at Strike. If not, you keep stock.
        # Yield on Cost (if we had basis) is better, but here we use Current Price as denominator for standard "Yield"
        static_return = premium / current_price
        annualized_yield = static_return * (365.0 / days_to_exp)
        
        # 2. Distance from Current Price (OTM %)
        otm_pct = (strike - current_price) / current_price
        
        # 3. Greeks Calculation using mibian (Black-Scholes)
        # We try to calculate Implied Volatility (IV) from our Premium first.
        # This is more robust than relying on Yahoo's 'impliedVolatility' which is often 0 for illiquid options.
        
        calculated_iv = np.nan
        try:
            # Only calculate if we have a valid premium and option implies some time value
            # Intrinsic value check: Premium must be > Intrinsic for valid IV
            intrinsic_value = max(0, current_price - strike)
            if premium > intrinsic_value:
                 # mibian expects percentage for volatility, but when solving for IV, it returns percentage
                 c_iv = mibian.BS([current_price, strike, risk_free_rate*100, days_to_exp], callPrice=premium)
                 calculated_iv = c_iv.impliedVolatility
        except:
             pass
        
        # Determine Final IV: Use calculated if valid, else Yahoo's, else fallback
        yahoo_iv = row['impliedVolatility'] * 100
        final_iv = yahoo_iv
        
        if not np.isnan(calculated_iv) and calculated_iv > 0:
             final_iv = calculated_iv
        
        delta = np.nan
        prob_itm = np.nan
        
        try:
            # mibian expects volatility as percentage (e.g. 50 for 50%)
            c = mibian.BS([current_price, strike, risk_free_rate*100, days_to_exp], volatility=final_iv)
            delta = c.callDelta
            prob_itm = delta 
        except:
            # Fallback if model fails: Estimate based on Moneyness
            # If Deep ITM -> 1.0, Deep OTM -> 0.0
            if current_price > strike:
                delta = 1.0
            else:
                delta = 0.0
            prob_itm = delta

        results.append({
            'strike': strike,
            'premium': premium,
            'bid': bid,
            'ask': ask,
            'last_price': last_price,
            'volume': row['volume'],
            'openInterest': row['openInterest'],
            'impliedVolatility': final_iv, # Store the actually used IV
            'annualized_yield': annualized_yield,
            'static_return': static_return,
            'days_to_exp': days_to_exp,
            'otm_pct': otm_pct,
            'delta': delta,
            'prob_itm': prob_itm
        })
        
    return pd.DataFrame(results)
