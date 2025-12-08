import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Car Lease Mileage Tracker", layout="wide")

def main():
    st.title("🚗 Car Lease Mileage Tracker")
    st.markdown("---")
    
    # Sidebar for inputs
    st.sidebar.header("Lease Information")
    
    # Input fields
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_month = st.selectbox("Month", range(1, 13), index=7, format_func=lambda x: f"{x:02d}")
        start_day = st.selectbox("Day", range(1, 32), index=3, format_func=lambda x: f"{x:02d}")
    with col2:
        start_year = st.number_input("Year", min_value=2020, max_value=2030, value=2025)
    
    lease_start = datetime(start_year, start_month, start_day)
    
    duration_years = st.sidebar.selectbox("Lease Duration (years)", [2, 3, 4, 5], index=1)
    annual_miles = st.sidebar.selectbox("Annual Mileage Allowance", [10000, 12000, 15000, 18000], index=0)
    current_miles = st.sidebar.number_input("Current Miles", min_value=0, value=1060)
    extra_price = st.sidebar.number_input("Price per Extra Mile ($)", min_value=0.0, value=0.25, step=0.01)
    
    # Calculate button
    if st.sidebar.button("Calculate", type="primary"):
        calculate_and_display(lease_start, duration_years, annual_miles, current_miles, extra_price)
    
    # Show initial message if no calculation yet
    if 'calculated' not in st.session_state:
        st.info("👆 Enter your lease details in the sidebar and click 'Calculate' to see your mileage analysis.")

def calculate_and_display(lease_start, duration_years, annual_miles, current_miles, extra_price):
    try:
        lease_end = lease_start.replace(year=lease_start.year + duration_years)
        today = datetime.now()
        
        # Validate inputs
        if lease_start > today:
            st.error("❌ Lease start date cannot be in the future")
            return
        
        # Calculate projections
        total_allowed_miles = annual_miles * duration_years
        lease_duration_days = (lease_end - lease_start).days
        days_elapsed = (today - lease_start).days
        
        if days_elapsed <= 0:
            st.error("❌ Lease hasn't started yet")
            return
        
        daily_allowed_miles = total_allowed_miles / lease_duration_days
        projected_miles_today = daily_allowed_miles * days_elapsed
        miles_difference = current_miles - projected_miles_today
        status = "OVER" if miles_difference > 0 else "UNDER"
        
        # Project to end
        daily_actual_rate = current_miles / days_elapsed
        projected_end_miles = daily_actual_rate * lease_duration_days
        overage_miles = max(0, projected_end_miles - total_allowed_miles)
        overage_fee = overage_miles * extra_price
        
        # Display results
        st.session_state.calculated = True
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Miles", f"{current_miles:,}")
        with col2:
            st.metric("Projected Today", f"{projected_miles_today:.0f}", 
                     f"{miles_difference:+.0f} miles")
        with col3:
            st.metric("Annual Pace", f"{(current_miles / days_elapsed * 365.25):.0f}")
        with col4:
            if overage_miles > 0:
                st.metric("Projected Overage", f"${overage_fee:.2f}", 
                         f"{overage_miles:.0f} miles")
            else:
                st.metric("Status", "✅ On Track")
        
        # Status alert
        if overage_miles > 0:
            st.error(f"⚠️ **WARNING**: You're on track to exceed your lease limit by {overage_miles:.0f} miles, costing ${overage_fee:.2f}")
        else:
            extra_miles = total_allowed_miles - projected_end_miles
            st.success(f"✅ **Good News**: You're staying within your limit with {extra_miles:.0f} miles to spare!")
        
        # Create the chart
        create_chart(lease_start, lease_end, total_allowed_miles, current_miles, 
                    today, projected_end_miles, projected_miles_today, 
                    daily_allowed_miles, daily_actual_rate)
        
        # Detailed summary
        st.markdown("---")
        st.subheader("📊 Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Current Status** ({today.strftime('%B %d, %Y')}):
            - Days into lease: {days_elapsed} days ({days_elapsed/365.25:.1f} years)
            - Current mileage: {current_miles:,} miles
            - Should be at: {projected_miles_today:.0f} miles
            - Difference: {abs(miles_difference):.0f} miles {status}
            - Daily pace: {daily_actual_rate:.1f} miles/day
            """)
        
        with col2:
            st.markdown(f"""
            **End-of-Lease Projection**:
            - Expected total: {projected_end_miles:.0f} miles
            - Lease allowance: {total_allowed_miles:,} miles
            - Overage: {overage_miles:.0f} miles
            - Penalty cost: ${overage_fee:.2f}
            - Days remaining: {lease_duration_days - days_elapsed} days
            """)
        
        # Recommendations
        st.subheader("💡 Recommendations")
        if overage_miles > 0:
            remaining_days = lease_duration_days - days_elapsed
            max_daily_rate = (total_allowed_miles - current_miles) / remaining_days if remaining_days > 0 else 0
            reduction_needed = daily_actual_rate - max_daily_rate
            
            st.warning(f"""
            **To stay within your lease limit:**
            - Reduce daily driving to: {max_daily_rate:.1f} miles/day
            - You need to cut back by: {reduction_needed:.1f} miles/day
            - Consider carpooling, public transport, or working from home more often
            """)
        else:
            extra_miles_available = total_allowed_miles - projected_end_miles
            remaining_days = lease_duration_days - days_elapsed
            extra_daily = extra_miles_available / remaining_days if remaining_days > 0 else 0
            
            st.success(f"""
            **You have room to drive more:**
            - Extra miles available: {extra_miles_available:.0f} miles
            - You could increase daily driving by: {extra_daily:.1f} miles/day
            - Keep up the good work!
            """)
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def create_chart(lease_start, lease_end, total_allowed_miles, current_miles, 
                today, projected_end_miles, projected_miles_today, 
                daily_allowed_miles, daily_actual_rate):
    
    # Create timeline data
    lease_duration_days = (lease_end - lease_start).days
    dates = pd.date_range(start=lease_start, end=lease_end, freq='D')
    
    # Allowance line
    allowance_miles = [(date - lease_start).days * daily_allowed_miles for date in dates]
    
    # Actual usage line (past and projected)
    actual_dates = [lease_start, today]
    actual_miles = [0, current_miles]
    
    # Projected line
    projected_dates = [today, lease_end]
    projected_miles_line = [current_miles, projected_end_miles]
    
    # Create the plot
    fig = go.Figure()
    
    # Allowance line
    fig.add_trace(go.Scatter(
        x=dates, y=allowance_miles,
        mode='lines',
        name='Lease Allowance',
        line=dict(color='blue', dash='dash', width=2),
        hovertemplate='<b>Allowance</b><br>Date: %{x}<br>Miles: %{y:,.0f}<extra></extra>'
    ))
    
    # Actual usage
    fig.add_trace(go.Scatter(
        x=actual_dates, y=actual_miles,
        mode='lines+markers',
        name='Actual Usage',
        line=dict(color='red', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Actual</b><br>Date: %{x}<br>Miles: %{y:,.0f}<extra></extra>'
    ))
    
    # Projected usage
    fig.add_trace(go.Scatter(
        x=projected_dates, y=projected_miles_line,
        mode='lines',
        name='Projected Usage',
        line=dict(color='red', dash='dot', width=2),
        hovertemplate='<b>Projected</b><br>Date: %{x}<br>Miles: %{y:,.0f}<extra></extra>'
    ))
    
    # Key points
    fig.add_trace(go.Scatter(
        x=[today], y=[current_miles],
        mode='markers',
        name=f'Today ({current_miles:,} mi)',
        marker=dict(color='red', size=12, symbol='circle'),
        hovertemplate='<b>Today</b><br>Date: %{x}<br>Miles: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=[today], y=[projected_miles_today],
        mode='markers',
        name=f'Should be ({projected_miles_today:.0f} mi)',
        marker=dict(color='blue', size=12, symbol='circle'),
        hovertemplate='<b>Should be at</b><br>Date: %{x}<br>Miles: %{y:,.0f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=[lease_end], y=[projected_end_miles],
        mode='markers',
        name=f'Projected End ({projected_end_miles:.0f} mi)',
        marker=dict(color='orange' if projected_end_miles > total_allowed_miles else 'green', 
                   size=12, symbol='diamond'),
        hovertemplate='<b>Projected End</b><br>Date: %{x}<br>Miles: %{y:,.0f}<extra></extra>'
    ))
    
    # Layout
    fig.update_layout(
        title=f'Lease Mileage Tracking: {lease_start.strftime("%b %Y")} - {lease_end.strftime("%b %Y")}',
        xaxis_title='Date',
        yaxis_title='Cumulative Miles',
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Add horizontal line for lease limit
    fig.add_hline(y=total_allowed_miles, line_dash="dash", line_color="gray", 
                  annotation_text=f"Lease Limit: {total_allowed_miles:,} mi")
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()