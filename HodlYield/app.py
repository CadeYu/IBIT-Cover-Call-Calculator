import streamlit as st
import pandas as pd
import plotly.express as px
from logic import get_current_price, get_option_dates, get_option_chain, calculate_metrics, get_risk_free_rate

st.set_page_config(page_title="HodlYield - IBIT Strategy", layout="wide")

# --- Sidebar ---
st.sidebar.title("HodlYield 🛡️")
st.sidebar.markdown("Bitcoin Maxi 为比特币最大主义者设计的低风险被动收入工具")

ticker = st.sidebar.text_input("Ticker Symbol", "IBIT")
cost_basis = st.sidebar.number_input("Cost Basis ($)", min_value=0.0, value=0.0, step=0.1, help="Your average purchase price. Used to warn against selling calls below cost.")

st.sidebar.markdown("---")
st.sidebar.subheader("Strategy Parameters")
max_delta = st.sidebar.slider("Max Delta (Risk)", 0.0, 1.0, 0.30, help="Delta approximates the probability of the option expiring ITM (Getting assigned). Bitcoin Maxis usually prefer < 0.3")
min_yield = st.sidebar.slider("Min Annualized Yield (%)", 0.0, 50.0, 5.0)

if st.sidebar.button("🧹 Clear Date Cache"):
    st.cache_data.clear()
    st.rerun()

# --- Caching Wrappers ---
@st.cache_data(ttl=60) # Cache price for 1 minute
def cached_get_current_price(t):
    return get_current_price(t)

@st.cache_data(ttl=3600) # Cache dates for 1 hour
def cached_get_option_dates(t):
    return get_option_dates(t)

@st.cache_data(ttl=300) # Cache chain for 5 minutes
def cached_get_option_chain(t, d):
    return get_option_chain(t, d)

@st.cache_data(ttl=86400) # Risk free rate rarely changes
def cached_get_risk_free_rate():
    return get_risk_free_rate()

# --- Main Logic ---
st.info("ℹ️ **数据来源**: 本工具使用 Yahoo Finance 数据，对应美国主流期权交易所 (如 CBOE, Nasdaq) 的 IBIT 期权市场。")

with st.expander("📚 新手指南：如何选择最好的期权？ (点击展开)"):
    st.markdown("""
    ### 1. 怎么看风险 (Risk)?
    我们使用 **Delta** 来衡量风险。
    - **Delta** 大致等于**期权被行权的概率** (失去 IBIT 筹码的概率)。
    - **Delta 0.20** 意味着大约只有 **20%** 的概率股价会涨破行权价。
    - **比特币最大主义者策略**: 通常选择 **Delta 0.15 - 0.25** 的期权。既能赚取权利金，又大概率能保住币。

    ### 2. 怎么看回报 (Annualized Yield)?
    不要只看权利金 (Premium) 是多少钱，要看 **年化收益率**。
    - 这里的年化收益率假设您**每周/每月**都成功卖出同样的期权。
    - 目标: 在低风险 (Delta < 0.3) 的情况下，寻找 **5% - 15%** 的年化收益。

    ### 3. 我该选哪一个?
    - **保守型**: 选 Delta < 0.15，虽然钱少 (可能只有年化 2-3%)，但几乎不会卖飞。
    - **稳健型 (推荐)**: 选 Delta 0.20 左右，年化收益通常不错，且保留了大部分上涨空间。
    - **激进型**: 选 Delta > 0.30，权利金很厚，但很容易卖飞 (币价大涨时您赚不到行权价以上的钱)。
    """)

if ticker:
    st.write(f"正在加载数据: {ticker}...") # Immediate feedback
    try:
        with st.spinner(f"正在获取 {ticker} 实时价格..."):
            current_price = cached_get_current_price(ticker)
        
        if current_price == 0:
             st.error(f"无法获取 {ticker} 价格。请检查代码是否正确或网络连接。")
        else:
            st.metric("Current Price (当前价格)", f"${current_price:.2f}")
            
            with st.spinner("正在获取期权链日期..."):
                dates = cached_get_option_dates(ticker)
                
            if not dates:
                st.warning("未找到期权数据 (No option chain data found).")
            else:
                selected_date = st.selectbox("Select Expiration Date", dates)
                
                if selected_date:
                    with st.spinner("Fetching Option Chain & Calculating Greeks..."):
                        calls = cached_get_option_chain(ticker, selected_date)
                        risk_free = cached_get_risk_free_rate()
                        df = calculate_metrics(calls, current_price, selected_date, risk_free)
                        
                        # --- Filters ---
                        # Filter out very deep ITM options that distort charts usually
                        df = df[df['strike'] > (current_price * 0.8)] 
                        
                    # --- Visualization: Risk/Reward Scatter Plot ---
                    st.subheader("Risk vs. Reward Analysis")
                    st.markdown("Select the 'Top Left' candidates: **Low Risk (Low Delta), High Yield**")
                    
                    # Filter for plot based on sidebar
                    plot_df = df[(df['delta'] <= 1.0) & (df['premium'] > 0)] # Filter out invalid/zero price data
                    
                    if plot_df.empty:
                        st.warning("⚠️ 该到期日的所有期权都没有报价 (权利金为 0)，无法绘制图表。这通常是因为该日期流动性太差。请尝试选择其他日期。")
                    else:
                        fig = px.scatter(
                            plot_df,
                            x="delta",
                            y="annualized_yield",
                            size="premium",
                            color="otm_pct",
                            hover_data=["strike", "premium", "static_return"],
                            labels={
                                "delta": "Risk (Delta / Prob ITM)",
                                "annualized_yield": "Annualized Yield (%)",
                                "otm_pct": "OTM %"
                            },
                            title=f"Yield vs. Risk (Delta) for {selected_date}",
                            color_continuous_scale="Viridis"
                        )
                        # Reverse X axis so "Safer" (Low Delta) is on the Left? 
                        # Actually standard is 0 to 1. 0 on left is intuitive "Low Risk".
                        fig.update_layout(xaxis_range=[0, 1.0])
                        
                        # Add a vertical line for User's Max Delta
                        fig.add_vline(x=max_delta, line_dash="dash", line_color="red", annotation_text="Max Risk Limit")
                        
                        st.plotly_chart(fig, use_container_width=True)

                    # --- Data Table ---
                    st.subheader("Detailed Option Chain")
                    
                    # Apply Highlight Logic
                    def highlight_risky(row):
                        # Red if Strike < Cost Basis (Risk of locking in loss)
                        if cost_basis > 0 and row['strike'] < cost_basis:
                            return ['background-color: rgba(255, 80, 80, 0.3)'] * len(row)
                        # Yellow if Delta > Max Delta
                        elif row['delta'] > max_delta:
                             return ['background-color: rgba(255, 255, 0, 0.2)'] * len(row)
                        # Green if "Ideal" (Delta < Max & Yield > Min & Strike > Cost)
                        elif row['delta'] <= max_delta and row['annualized_yield'] >= (min_yield/100.0) and (cost_basis == 0 or row['strike'] >= cost_basis):
                            return ['background-color: rgba(0, 255, 0, 0.2)'] * len(row)
                        else:
                            return [''] * len(row)

                    # Format columns for display
                    # Format columns for display using Styler to keep underlying data numeric for highlighting
                    display_cols = ['strike', 'bid', 'ask', 'last_price', 'delta', 'otm_pct', 'annualized_yield', 'static_return', 'premium']
                    display_df = df[display_cols].copy()
                    
                    styler = display_df.style.apply(highlight_risky, axis=1).format({
                        'annualized_yield': '{:.2%}',
                        'static_return': '{:.2%}',
                        'otm_pct': '{:.2%}',
                        'delta': '{:.2f}',
                        'premium': '${:.2f}',
                        'strike': '${:.2f}',
                        'bid': '${:.2f}',
                        'ask': '${:.2f}',
                        'last_price': '${:.2f}'
                    })

                    st.dataframe(styler, use_container_width=True)
                    
                    if cost_basis == 0:
                        st.info("💡 **提示**: 在左侧侧边栏输入您的 **持仓成本 (Cost Basis)** ($)，系统会自动用红色高亮低于成本的行权价，防止卖飞亏损。")

                    st.markdown("""
                    **Legend:**
                    - 🟥 **Red Background**: Strike Price below your Cost Basis (Capital Loss Risk).
                    - 🟨 **Yellow Background**: Risk (Delta) higher than your preference.
                    - 🟩 **Green Background**: Meets all your criteria (Safe & Yielding).
                    """)

    except Exception as e:
        st.error(f"Error: {e}")
