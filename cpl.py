import streamlit as st
import pandas as pd

# --- Initialize Session State (New) ---
# Check if results are already calculated and stored
if 'calc_results' not in st.session_state:
    st.session_state.calc_results = None

# --- Page Configuration ---
st.set_page_config(
    page_title="Agent Compensation Calculator",
    page_icon="🛡️",
    layout="wide"
)

# --- Custom CSS for Prudential Branding ---
# Colors: Prudential Red (#CC0000), Teal/Cyan (#009999), Dark Grey (#333333)
st.markdown("""
    <style>
    .main {
        background-color: #f4f4f4;
    }
    h1, h2, h3 {
        color: #333333;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    /* Header Style */
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Custom Buttons and Highlights */
    .stButton>button {
        background-color: #CC0000;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        height: 3em;
        width: 100%;
        border: none;
    }
    .stButton>button:hover {
        background-color: #990000;
        color: white;
    }
    /* Metric Cards */
    .metric-card {
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .bg-red { background-color: #CC0000; }
    .bg-teal { background-color: #009999; }
    .bg-dark { background-color: #333333; }
    /* Input Section Container */
    .input-section {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #CC0000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)


# --- Helper Functions ---
def get_base_rate(monthly_fyc):
    """Determines Base Rate based on Monthly Average FYC"""
    if monthly_fyc < 2000:
        return 0
    elif 2000 <= monthly_fyc <= 2333:
        return 0
    elif 2333 < monthly_fyc <= 5000:
        return 0.15
    elif 5000 < monthly_fyc <= 6667:
        return 0.20
    else:  # > 6667
        return 0.25


def get_persistency_multiplier(rate):
    """Determines Persistency Multiplier"""
    if 0 <= rate < 0.5:
        return 0
    else:
        return 1


def get_active_month_multiplier(months):
    """Determines Active Month Multiplier"""
    if months == 3:
        return 1.2
    else:
        return 0


# --- Main Application ---
def main():
    # Header
    # st.image("https://www.prudential.com.gh/themes/custom/prudential/logo.svg", width=150)
    st.markdown("<h1 style='color: #CC0000;'>Agent Compensation Calculator</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Layout: 3 Columns
    col_input, col_process, col_output = st.columns([1, 1, 1], gap="large")

    # ==========================================
    # COLUMN 1: INPUTS
    # ==========================================
    with col_input:
        st.markdown("### 📝 Input Parameters")
        with st.container():
            # 1. Rank
            rank = st.selectbox("Agent Rank", options=["Agent"])

            # 2. Join Date
            join_date = st.text_input("Join Date", value="2000.12.01", help="Format: YYYY.MM.DD")

            st.markdown("---")
            st.markdown("#### 📊 Quarterly Sales (FYP)")

            # Product Definitions
            risk_products = ["Classic", "Premier", "Prudent", "HCP"]
            savings_products = ["Pruwealth", "Education", "Ultimate Education Plus"]
            fyp_inputs = {}

            # Inputs for Risk Products
            st.markdown("**Risk Products**")
            for prod in risk_products:
                fyp_inputs[prod] = st.number_input(f"{prod} (Risk)", min_value=0.0, step=100.0, key=prod)

            st.markdown("**Savings Products**")
            for prod in savings_products:
                fyp_inputs[prod] = st.number_input(f"{prod} (Savings)", min_value=0.0, step=100.0, key=prod)

            st.markdown("---")
            st.markdown("#### 📈 Performance Metrics")

            # 4. Persistency Rate
            persistency_rate = st.number_input("Avg. Monthly Persistency Rate (0-1)", min_value=0.0, max_value=1.0,
                                               value=0.8, step=0.01)

            # 5. Case Number
            case_number = st.number_input("Sales Case Number", min_value=0, step=1)

            # 6. Active Months
            active_months = st.number_input("No. of Active Months", min_value=0, max_value=3, step=1)

            # --- Calculation Trigger & Storage (Modified) ---
            # Store the input values needed for recalculation in session state
            st.session_state.current_inputs = {
                'fyp_inputs': fyp_inputs,
                'risk_products': risk_products,
                'savings_products': savings_products,
                'persistency_rate': persistency_rate,
                'case_number': case_number,
                'active_months': active_months
            }

            # Calculate Button
            if st.button("Calculate Compensation"):
                # --- CALCULATION LOGIC (Hidden processing) ---
                # Calculate Totals
                total_fyp_risk = sum(fyp_inputs[p] for p in risk_products)
                total_fyp_saving = sum(fyp_inputs[p] for p in savings_products)

                # 1. Total FYC Calculation
                total_fyc = (total_fyp_saving * 0.12) + (total_fyp_risk * 0.36)

                # Monthly Average FYC (for Base Rate lookup)
                monthly_avg_fyc = total_fyc / 3

                # Get Multipliers and Rates
                base_rate = get_base_rate(monthly_avg_fyc)
                title_multiplier = 1
                persistency_multiplier = get_persistency_multiplier(persistency_rate)
                active_month_multiplier = get_active_month_multiplier(active_months)
                cases_multiplier = 0

                # Eligibility Check for Production Bonus
                is_eligible = (total_fyc >= 7000) and (persistency_rate >= 0.5)

                if is_eligible:
                    # Base Production Bonus
                    base_prod_bonus = total_fyc * base_rate * title_multiplier * persistency_rate

                    # Extras
                    persistency_extra_bonus = base_prod_bonus * persistency_multiplier
                    consistency_extra_bonus = base_prod_bonus * active_month_multiplier
                    productivity_bonus = base_prod_bonus * cases_multiplier

                    total_prod_bonus = base_prod_bonus + persistency_extra_bonus + consistency_extra_bonus + productivity_bonus
                else:
                    base_prod_bonus = 0
                    persistency_extra_bonus = 0
                    consistency_extra_bonus = 0
                    productivity_bonus = 0
                    total_prod_bonus = 0

                # Total Income
                total_income = total_fyc + total_prod_bonus

                # --- Store Results in Session State (New) ---
                st.session_state.calc_results = {
                    'total_fyp_risk': total_fyp_risk,
                    'total_fyp_saving': total_fyp_saving,
                    'total_fyc': total_fyc,
                    'monthly_avg_fyc': monthly_avg_fyc,
                    'base_rate': base_rate,
                    'title_multiplier': title_multiplier,
                    'persistency_rate': persistency_rate,
                    'persistency_multiplier': persistency_multiplier,
                    'active_months': active_months,
                    'active_month_multiplier': active_month_multiplier,
                    'cases_multiplier': cases_multiplier,
                    'base_prod_bonus': base_prod_bonus,
                    'persistency_extra_bonus': persistency_extra_bonus,
                    'consistency_extra_bonus': consistency_extra_bonus,
                    'productivity_bonus': productivity_bonus,
                    'total_prod_bonus': total_prod_bonus,
                    'total_income': total_income,
                    'is_eligible': is_eligible
                }

    # ==========================================
    # COLUMN 2: CALCULATION PROCESS
    # ==========================================
    with col_process:
        st.markdown("### 🧮 Calculation Logic")

        # --- Display Logic based on Session State (Modified) ---
        results = st.session_state.calc_results

        if results is not None:  # If calculation has been done
            st.success("Calculation Complete!")

            with st.expander("1. FYC Calculation", expanded=True):
                st.latex(r"FYC = (FYP_{saving} \times 12\%) + (FYP_{risk} \times 36\%)")
                st.write(f"- **Total Risk FYP:** {results['total_fyp_risk']:,.2f}")
                st.write(f"- **Total Savings FYP:** {results['total_fyp_saving']:,.2f}")
                st.write(f"- **Result:** {results['total_fyc']:,.2f}")

            with st.expander("2. Parameters & Eligibility", expanded=True):
                st.write(f"- **Monthly Avg FYC:** {results['monthly_avg_fyc']:,.2f}")
                st.write(f"- **Base Rate (Table Lookup):** {results['base_rate']:.2%}")
                st.write(f"- **Eligibility (FYC≥7k & Rate≥0.5):** {'✅ Yes' if results['is_eligible'] else '❌ No'}")

            with st.expander("3. Bonus Breakdown", expanded=True):
                if results['is_eligible']:
                    st.write(f"**Base Production Bonus:**")
                    st.latex(r"Base \times Rate \times Title \times P\_Rate")
                    st.write(
                        f"= {results['total_fyc']:,.2f} × {results['base_rate']} × 1 × {results['persistency_rate']} = **{results['base_prod_bonus']:,.2f}**")
                    st.write("---")
                    st.write(
                        f"**Persistency Extra:** {results['base_prod_bonus']:,.2f} × {results['persistency_multiplier']} = {results['persistency_extra_bonus']:,.2f}")
                    st.write(
                        f"**Consistency Extra:** {results['base_prod_bonus']:,.2f} × {results['active_month_multiplier']} = {results['consistency_extra_bonus']:,.2f}")
                    st.write(
                        f"**Productivity Bonus:** {results['base_prod_bonus']:,.2f} × {results['cases_multiplier']} = {results['productivity_bonus']:,.2f}")
                else:
                    st.info("Production Bonus is 0 because eligibility criteria were not met.")
        else:
            st.info("Please enter inputs and click Calculate to see logic.")

    # ==========================================
    # COLUMN 3: OUTPUT
    # ==========================================
    with col_output:
        st.markdown("### 💰 Final Results")

        # --- Display Logic based on Session State (Modified) ---
        results = st.session_state.calc_results

        if results is not None:  # If calculation has been done
            # Output Cards
            st.markdown(f"""
                <div class="metric-card bg-dark">
                    <h4>Total FYC</h4>
                    <h2>{results['total_fyc']:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-card bg-teal">
                    <h4>Total Production Bonus</h4>
                    <h2>{results['total_prod_bonus']:,.2f}</h2>
                    <small>Base: {results['base_prod_bonus']:,.2f} | Extra: {results['persistency_extra_bonus'] + results['consistency_extra_bonus']:,.2f}</small>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="metric-card bg-red">
                    <h4>Total Income</h4>
                    <h2>{results['total_income']:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)

            # Summary Table
            st.markdown("#### Summary Details")
            summary_data = {
                "Metric": ["Total Risk FYP", "Total Savings FYP", "Monthly Avg FYC", "Base Rate",
                           "Active Month Multiplier", "Persistency Multiplier"],
                "Value": [f"{results['total_fyp_risk']:,.2f}", f"{results['total_fyp_saving']:,.2f}",
                          f"{results['monthly_avg_fyc']:,.2f}", f"{results['base_rate']:.2%}",
                          results['active_month_multiplier'], results['persistency_multiplier']]
            }
            st.table(pd.DataFrame(summary_data))
        else:
            st.info("Please enter inputs and click Calculate to see results.")


if __name__ == "__main__":
    main()