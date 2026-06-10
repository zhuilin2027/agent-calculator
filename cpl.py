import streamlit as st
import pandas as pd

# 设置页面为宽屏模式，解决左右留白问题
st.set_page_config(layout="wide", page_title="Ghana Compensation Model", page_icon="🛡️")

# ==========================================
# CSS STYLES (Strictly following cpl.txt)
# ==========================================
st.markdown("""
<style>
    .metric-card {
        padding: 15px;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card h4 { font-size: 18px; margin: 0; font-weight: 600; }
    .metric-card h2 { font-size: 26px; margin: 5px 0; font-weight: bold; }
    .metric-card small { font-size: 14px; display: block; margin-top: 8px; opacity: 0.9; line-height: 1.5; }

    .bg-dark { background-color: #2C3E50; }
    .bg-teal { background-color: #16A085; }
    .bg-red { background-color: #CC0000; }
    .bg-blue { background-color: #2980B9; }
    .bg-orange { background-color: #D35400; }
    .bg-purple { background-color: #8E44AD; }

    .input-section {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #CC0000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stDataFrame { width: 100%; }

    /* 隐藏 form 默认的提交成功提示，保持界面干净 */
    .stForm button[data-testid="stFormSubmitButton"] p { font-weight: 600; }

    /* 登录页面样式微调 */
    .login-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# CALCULATION LOGIC
# ==========================================

def calculate_old_logic(inputs):
    """
    Old Logic based on '加纳项目计算模型@0605output2.docx'
    """
    rank = inputs['rank']
    total_fyc = (inputs['fyp_risk'] * 0.36) + (inputs['fyp_saving'] * 0.12)
    total_ryc = inputs['total_ryc']
    base_commission = total_fyc + total_ryc

    results = {
        'base_commission': base_commission,
        'total_fyc': total_fyc,
        'total_ryc': total_ryc,
        'direct_or': 0,
        'base_direct_or': 0,
        'indirect_or': 0,
        'total_income': base_commission,
        'process_metrics': []
    }

    results['process_metrics'].append({
        'Metric': 'Total FYC',
        'Value': total_fyc,
        'Conditions': 'FYP_Risk * 36% + FYP_Saving * 12%',
        'Status': 'Calculated'
    })

    is_moa_mom = rank in ['MoA', 'MoM']
    if is_moa_mom:
        base_direct_or = (inputs['direct_fyc'] + inputs['direct_ryc']) * 0.20
        results['direct_or'] = base_direct_or
        results['base_direct_or'] = base_direct_or
        results['total_income'] += base_direct_or
        results['process_metrics'].append({
            'Metric': 'Base direct OR',
            'Value': base_direct_or,
            'Conditions': 'MoA or MoM (Unified 20% rate)',
            'Status': 'Eligible'
        })

    if rank == 'MoM':
        indirect_or = (inputs['indirect_fyc'] + inputs['indirect_ryc']) * 0.15
        results['indirect_or'] = indirect_or
        results['total_income'] += indirect_or
        results['process_metrics'].append({
            'Metric': 'Indirect OR',
            'Value': indirect_or,
            'Conditions': 'MoM (15% rate)',
            'Status': 'Eligible'
        })

    return results


def calculate_new_logic(inputs):
    """
    New Logic based on '加纳项目计算模型@0605output1.docx'
    """
    rank = inputs['rank']
    total_fyc = (inputs['fyp_risk'] * 0.36) + (inputs['fyp_saving'] * 0.12)
    total_ryc = inputs['total_ryc']
    base_commission = total_fyc + total_ryc

    results = {
        'base_commission': base_commission,
        'total_fyc': total_fyc,
        'total_ryc': total_ryc,
        'total_prod_bonus': 0,
        'base_q_bonus': 0,
        'consistency_bonus': 0,
        'productivity_bonus': 0,
        'direct_or': 0,
        'base_direct_or': 0,
        'active_agent_bonus': 0,
        'indirect_or': 0,
        'leader_bonus': 0,
        'rookie_moa_or': 0,
        'spinoff_or': 0,
        'franchise_or': 0,
        'total_income': base_commission,
        'process_metrics': []
    }

    # 1. Production Bonus (Agent only)
    is_agent = (rank == 'Agent')
    fyc_eligible = total_fyc >= 7000
    ape_eligible = inputs['ape_40k_YN'] == 'Y'
    persist_eligible = inputs['persistency_YN'] == 'Y'
    prod_bonus_eligible = is_agent and fyc_eligible and ape_eligible and persist_eligible

    if total_fyc >= 50000:
        rate = 0.30
    elif total_fyc >= 35000:
        rate = 0.20
    elif total_fyc >= 20000:
        rate = 0.10
    elif total_fyc >= 7000:
        rate = 0.05
    else:
        rate = 0.0

    base_q_bonus = total_fyc * rate if prod_bonus_eligible else 0

    consistency_eligible = inputs['active_months'] == 3
    consistency_bonus = base_q_bonus * 0.15 if (prod_bonus_eligible and consistency_eligible) else 0

    productivity_eligible = inputs['avg_cases'] >= 10
    productivity_bonus = base_q_bonus * 0.15 if (prod_bonus_eligible and productivity_eligible) else 0

    total_prod_bonus = base_q_bonus + consistency_bonus + productivity_bonus

    results['total_prod_bonus'] = total_prod_bonus
    results['base_q_bonus'] = base_q_bonus
    results['consistency_bonus'] = consistency_bonus
    results['productivity_bonus'] = productivity_bonus
    results['total_income'] += total_prod_bonus

    if is_agent:
        results['process_metrics'].append({
            'Metric': 'Base quarterly bonus', 'Value': base_q_bonus,
            'Conditions': '1）Agent 2）FYC ≥ 7,000 3）APE ≥ 40,000 4）Persistency ≥ 75%',
            'Status': 'Eligible' if prod_bonus_eligible else 'Not Eligible'
        })
        results['process_metrics'].append({
            'Metric': 'Consistency extra', 'Value': consistency_bonus,
            'Conditions': 'Active months per quarter = 3',
            'Status': 'Eligible' if consistency_eligible else 'Not Eligible'
        })
        results['process_metrics'].append({
            'Metric': 'Productivity extra', 'Value': productivity_bonus,
            'Conditions': 'Monthly avg cases sold ≥ 10',
            'Status': 'Eligible' if productivity_eligible else 'Not Eligible'
        })

    # 2. Direct OR (MoA, MoM)
    is_moa_mom = rank in ['MoA', 'MoM']
    if is_moa_mom:
        base_direct_rate = 0.22 if rank == 'MoM' else 0.20
        base_direct_or = (inputs['direct_fyc'] + inputs['direct_ryc']) * base_direct_rate

        active_agent_eligible = inputs['direct_persist_YN'] == 'Y' and inputs['active_agents'] >= 9
        agent_mult = 0.20 if (active_agent_eligible and inputs['active_agents'] >= 15) else (
            0.10 if active_agent_eligible else 0.0)
        active_agent_bonus = base_direct_or * agent_mult

        direct_or = base_direct_or + active_agent_bonus
        results['direct_or'] = direct_or
        results['base_direct_or'] = base_direct_or
        results['active_agent_bonus'] = active_agent_bonus
        results['total_income'] += direct_or

        results['process_metrics'].append({
            'Metric': 'Base direct OR', 'Value': base_direct_or,
            'Conditions': 'MoA or MoM', 'Status': 'Eligible'
        })
        results['process_metrics'].append({
            'Metric': 'Active agent extra', 'Value': active_agent_bonus,
            'Conditions': '1）Direct Persistency ≥ 75% 2）Active agents ≥ 9',
            'Status': 'Eligible' if active_agent_eligible else 'Not Eligible'
        })

    # 3. Indirect OR (MoM only)
    if rank == 'MoM':
        indirect_or = (inputs['indirect_fyc'] + inputs['indirect_ryc']) * 0.15
        results['indirect_or'] = indirect_or
        results['total_income'] += indirect_or
        results['process_metrics'].append({
            'Metric': 'Indirect OR', 'Value': indirect_or,
            'Conditions': 'MoM', 'Status': 'Eligible'
        })

    # 4. Leader Bonus (MoA, MoM)
    if is_moa_mom:
        leader_eligible = inputs['direct_ape_growth_YN'] == 'Y' and inputs['direct_persist_YN'] == 'Y'
        leader_rate = 0.22 if rank == 'MoM' else 0.20
        leader_bonus = inputs['direct_prod_bonus'] * leader_rate if leader_eligible else 0
        results['leader_bonus'] = leader_bonus
        results['total_income'] += leader_bonus
        results['process_metrics'].append({
            'Metric': 'Leader Bonus', 'Value': leader_bonus,
            'Conditions': '1）MoA/MoM 2）APE growth > 0% 3）Persistency ≥ 75%',
            'Status': 'Eligible' if leader_eligible else 'Not Eligible'
        })

    # 5. Rookie MoA OR (MoA only)
    if rank == 'MoA':
        rookie_eligible = inputs['promo_18m_YN'] == 'Y'
        rookie_or = inputs['qualified_recruits'] * 888 * 0.20 if rookie_eligible else 0
        results['rookie_moa_or'] = rookie_or
        results['total_income'] += rookie_or
        results['process_metrics'].append({
            'Metric': 'Rookie MoA OR', 'Value': rookie_or,
            'Conditions': '1）MoA 2）Promotion date < 18 months',
            'Status': 'Eligible' if rookie_eligible else 'Not Eligible'
        })

    # 6. Spin-off OR (MoA, MoM)
    if is_moa_mom:
        spinoff_or = inputs['new_leaders'] * 11000 * 0.15
        results['spinoff_or'] = spinoff_or
        results['total_income'] += spinoff_or
        results['process_metrics'].append({
            'Metric': 'Spin-off OR', 'Value': spinoff_or,
            'Conditions': 'MoA or MoM', 'Status': 'Eligible'
        })

    # 7. Franchise Growth OR (MoM only)
    if rank == 'MoM':
        franchise_eligible = inputs['ape_growth_30_YN'] == 'Y' and inputs['case_growth_15_YN'] == 'Y'
        franchise_or = inputs['total_unit_ape'] * 0.005 if franchise_eligible else 0
        results['franchise_or'] = franchise_or
        results['total_income'] += franchise_or
        results['process_metrics'].append({
            'Metric': 'Franchise Growth OR', 'Value': franchise_or,
            'Conditions': '1）MoM 2）APE growth ≥ 30% 3）Case growth ≥ 15%',
            'Status': 'Eligible' if franchise_eligible else 'Not Eligible'
        })

    return results


# ==========================================
# CACHE WRAPPERS (Optimization for Concurrency)
# ==========================================
@st.cache_data(show_spinner=False)
def _cached_old_logic(inputs_tuple):
    """内部缓存函数，接收可哈希的 tuple"""
    return calculate_old_logic(dict(inputs_tuple))


@st.cache_data(show_spinner=False)
def _cached_new_logic(inputs_tuple):
    """内部缓存函数，接收可哈希的 tuple"""
    return calculate_new_logic(dict(inputs_tuple))


def get_old_logic_results(inputs):
    """将 dict 转换为 tuple 以支持 Streamlit 的哈希缓存机制"""
    return _cached_old_logic(tuple(sorted(inputs.items())))


def get_new_logic_results(inputs):
    """将 dict 转换为 tuple 以支持 Streamlit 的哈希缓存机制"""
    return _cached_new_logic(tuple(sorted(inputs.items())))


# ==========================================
# UI RENDERING FUNCTIONS
# ==========================================

def render_input(prefix):
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.subheader(f"📝 Input Parameters ({prefix})")

    rank = st.selectbox("👤 Agent Rank", ["Agent", "MoA", "MoM"], key=f"{prefix}_rank")
    col1, col2 = st.columns(2)
    fyp_risk = col1.number_input("⚠️ FYP Risk", min_value=0.0, value=0.0, step=100.0, key=f"{prefix}_fyp_risk")
    fyp_saving = col2.number_input("💰 FYP Saving", min_value=0.0, value=0.0, step=100.0, key=f"{prefix}_fyp_saving")
    total_ryc = st.number_input("🔄 Total RYC (Direct Input)", min_value=0.0, value=0.0, step=100.0,
                                key=f"{prefix}_total_ryc")

    inputs = {
        'rank': rank, 'fyp_risk': fyp_risk, 'fyp_saving': fyp_saving, 'total_ryc': total_ryc,
        'persistency_YN': 'N', 'ape_40k_YN': 'N', 'active_months': 0, 'avg_cases': 0,
        'direct_fyc': 0, 'direct_ryc': 0, 'direct_persist_YN': 'N', 'direct_ape_growth_YN': 'N',
        'active_agents': 0, 'direct_prod_bonus': 0, 'new_leaders': 0,
        'promo_18m_YN': 'N', 'qualified_recruits': 0,
        'indirect_fyc': 0, 'indirect_ryc': 0, 'ape_growth_30_YN': 'N', 'case_growth_15_YN': 'N', 'total_unit_ape': 0
    }

    if rank == 'Agent':
        st.markdown("#### 🎯 Agent Metrics")
        c1, c2 = st.columns(2)
        inputs['persistency_YN'] = c1.selectbox("📊 Avg Monthly Persistency ≥75%", ["N", "Y"], key=f"{prefix}_p_yn")
        inputs['ape_40k_YN'] = c2.selectbox("📈 Quarterly APE ≥40,000", ["N", "Y"], key=f"{prefix}_ape_yn")
        c3, c4 = st.columns(2)
        inputs['active_months'] = c3.number_input("🗓️ Active months per quarter", 0, 3, 0, key=f"{prefix}_am")
        inputs['avg_cases'] = c4.number_input("📝 Monthly avg cases sold", 0.0, step=1.0, key=f"{prefix}_ac")

    if rank in ['MoA', 'MoM']:
        st.markdown("#### 👥 MoA / MoM Team Metrics")
        c1, c2 = st.columns(2)
        inputs['direct_fyc'] = c1.number_input("💼 Direct team FYC", 0.0, step=100.0, key=f"{prefix}_dfyc")
        inputs['direct_ryc'] = c2.number_input("💼 Direct team RYC", 0.0, step=100.0, key=f"{prefix}_dryc")
        c3, c4 = st.columns(2)
        inputs['direct_persist_YN'] = c3.selectbox("📊 Direct Persistency ≥75%", ["N", "Y"], key=f"{prefix}_dp_yn")
        inputs['direct_ape_growth_YN'] = c4.selectbox("📈 Direct APE growth > 0%", ["N", "Y"], key=f"{prefix}_dag_yn")
        c5, c6, c7 = st.columns(3)
        inputs['active_agents'] = c5.number_input("🏃 Active agents", 0, step=1, key=f"{prefix}_aa")
        inputs['direct_prod_bonus'] = c6.number_input("🎁 Direct prod bonus", 0.0, step=100.0, key=f"{prefix}_dpb")
        inputs['new_leaders'] = c7.number_input("🌟 1st year new leaders", 0, step=1, key=f"{prefix}_nl")

    if rank == 'MoA':
        st.markdown("#### 🎓 MoA Specific Metrics")
        c1, c2 = st.columns(2)
        inputs['promo_18m_YN'] = c1.selectbox("⏱️ Promotion < 18 months", ["N", "Y"], key=f"{prefix}_pr_yn")
        inputs['qualified_recruits'] = c2.number_input("🧑‍🎓 Qualified recruits", 0, step=1, key=f"{prefix}_qr")

    if rank == 'MoM':
        st.markdown("#### 🌐 MoM Specific Metrics")
        c1, c2 = st.columns(2)
        inputs['indirect_fyc'] = c1.number_input("🔗 Indirect team FYC", 0.0, step=100.0, key=f"{prefix}_ifyc")
        inputs['indirect_ryc'] = c2.number_input("🔗 Indirect team RYC", 0.0, step=100.0, key=f"{prefix}_iryc")
        c3, c4 = st.columns(2)
        inputs['ape_growth_30_YN'] = c3.selectbox("🚀 Unit APE growth ≥30%", ["N", "Y"], key=f"{prefix}_ag30_yn")
        inputs['case_growth_15_YN'] = c4.selectbox("📈 Unit case growth ≥15%", ["N", "Y"], key=f"{prefix}_cg15_yn")
        inputs['total_unit_ape'] = st.number_input("🏢 Total unit APE", 0.0, step=1000.0, key=f"{prefix}_tua")

    st.markdown('</div>', unsafe_allow_html=True)
    return inputs


def render_metric_card(title, value, bg_class, subtext=""):
    st.markdown(f"""
    <div class="metric-card {bg_class}">
        <h4>{title}</h4>
        <h2>{value:,.2f}</h2>
        {f'<small>{subtext}</small>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)


def render_single_output(results, title, is_new_logic):
    st.subheader(title)
    if is_new_logic:
        render_metric_card("Total Income", results['total_income'], "bg-dark")

        bc_sub = f"Total FYC: {results['total_fyc']:,.2f} | Total RYC: {results['total_ryc']:,.2f}"
        render_metric_card("Base Commission", results['base_commission'], "bg-teal", bc_sub)

        pb_sub = f"Base: {results['base_q_bonus']:,.2f} | Consistency: {results['consistency_bonus']:,.2f} | Productivity: {results['productivity_bonus']:,.2f}"
        render_metric_card("Production Bonus", results['total_prod_bonus'], "bg-red", pb_sub)

        dor_sub = f"Base: {results['base_direct_or']:,.2f} | Active Agent Extra: {results['active_agent_bonus']:,.2f}"
        render_metric_card("Direct OR", results['direct_or'], "bg-blue", dor_sub)

        render_metric_card("Indirect OR", results['indirect_or'], "bg-orange")
        render_metric_card("Leader Bonus", results['leader_bonus'], "bg-purple")
    else:
        render_metric_card("Total Income", results['total_income'], "bg-dark")

        bc_sub = f"Total FYC: {results['total_fyc']:,.2f} | Total RYC: {results['total_ryc']:,.2f}"
        render_metric_card("Base Commission", results['base_commission'], "bg-teal", bc_sub)

        dor_sub = f"Base: {results['base_direct_or']:,.2f}"
        render_metric_card("Direct OR", results['direct_or'], "bg-blue", dor_sub)

        render_metric_card("Indirect OR", results['indirect_or'], "bg-orange")

    if results['process_metrics']:
        df = pd.DataFrame(results['process_metrics'])
        st.table(df)


# ==========================================
# LOGIN PAGE
# ==========================================
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #CC0000;'>🛡️ Ghana Compensation Model</h1>",
                unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555;'>Please login to continue</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submit:
                if username == "stephenzhong" and password == "stephenzhongcool":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")


# ==========================================
# MAIN APP LAYOUT
# ==========================================
def main():
    # 1. 鉴权拦截：如果未登录，则显示登录页并终止后续渲染
    if not st.session_state.get("logged_in", False):
        login_page()
        return

    # 2. 侧边栏：显示当前用户及退出按钮（不破坏主页面的宽屏布局）
    with st.sidebar:
        st.markdown("### 👤 Account")
        st.success("Logged in as **stephenzhong**")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 3. 原有主界面逻辑
    st.markdown("<h1 style='color: #CC0000;'>Ghana Compensation Model Comparison Tool</h1>", unsafe_allow_html=True)
    st.markdown("Compare Scenario 1 and Scenario 2 side-by-side with Old Logic and New Logic.")

    # Scenario 1
    st.header("Scenario 1")
    col_in1, col_old1, col_new1 = st.columns([1, 2, 2])
    with col_in1:
        with st.form(key="form_s1"):
            inputs1 = render_input("S1")
            submitted1 = st.form_submit_button("Calculate Scenario 1", use_container_width=True)
            if submitted1:
                st.session_state['s1_old'] = get_old_logic_results(inputs1)
                st.session_state['s1_new'] = get_new_logic_results(inputs1)

    with col_old1:
        if 's1_old' in st.session_state:
            render_single_output(st.session_state['s1_old'], "💰 Output 1 (Old Logic)", False)

    with col_new1:
        if 's1_new' in st.session_state:
            render_single_output(st.session_state['s1_new'], "💰 Output 2 (New Logic)", True)

    st.markdown("---")

    # Scenario 2
    st.header("Scenario 2")
    col_in2, col_old2, col_new2 = st.columns([1, 2, 2])
    with col_in2:
        with st.form(key="form_s2"):
            inputs2 = render_input("S2")
            submitted2 = st.form_submit_button("Calculate Scenario 2", use_container_width=True)
            if submitted2:
                st.session_state['s2_old'] = get_old_logic_results(inputs2)
                st.session_state['s2_new'] = get_new_logic_results(inputs2)

    with col_old2:
        if 's2_old' in st.session_state:
            render_single_output(st.session_state['s2_old'], "💰 Output 1 (Old Logic)", False)

    with col_new2:
        if 's2_new' in st.session_state:
            render_single_output(st.session_state['s2_new'], "💰 Output 2 (New Logic)", True)


if __name__ == "__main__":
    main()
