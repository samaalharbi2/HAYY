"""BALAGH: interactive dashboard for municipal service requests.

Reads the Gold layer in BigQuery only.  Run from the repo root:  streamlit run dashboard/app.py
"""
import os

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.cloud import bigquery

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "balagh-510905")
GOLD = f"{PROJECT_ID}.balagh_gold"

st.set_page_config(page_title="BALAGH | بَلاغ", page_icon="📍", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- brand (from the BALAGH pitch deck)
NAVY, PANEL, LINE, TEXT, MUTED = "#0F1A2E", "#17233B", "#2A3756", "#E8EDF5", "#93A0B8"
GOLDEN, GREEN, BLUE, RED = "#FFC72C", "#4CAF50", "#5B8DEF", "#FF6B6B"
GROUP_COLORS = {"Effective": GREEN, "Root-Cause Attention": GOLDEN, "Operational Delay": BLUE, "Priority Issue": RED}
GROUP_ORDER = list(GROUP_COLORS)
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
}

# ---------------------------------------------------------------- text: one language per page, never mixed
T = {
    "en": {
        "name": "BALAGH", "switch": "العربية",
        "subtitle": "Interactive dashboard for municipal service requests",
        "goal": "Goal: help customer-experience teams find requests that are closed but come back, "
                "so root causes are fixed and repeat complaints go down.",
        "period": "Period", "city": "City: Riyadh", "city_hint": "Built for any city. Riyadh data is available today.",
        "tabs": ["Overview", "Where to act", "Neighborhood map", "Data reliability"],
        "steps": ["Received", "Processed", "Closed", "Repeated?"],
        "received_sub": "service requests", "processed_sub": "completion rate", "processed_np": "status not published",
        "closed_sub": "median time to close", "repeated_sub": "flagged as repeated",
        "not_published": "Not published", "hours": "h", "vs": "vs", "pp": "pts",
        "summary": "In {p}, <b>{n} request types</b> are closed but keep coming back, or close slowly and repeat. "
                   "Together they are <b>{share:.0%} of all requests</b>.",
        "c_groups": "Requests by resolution group", "c_domains": "Service domains",
        "c_trend": "Monthly requests and repeat rate", "c_repeated": "Most repeated request types",
        "c_domains_cap": "Label: share of requests flagged as repeated.",
        "c_repeated_cap": "Number of requests flagged as repeated.",
        "requests": "Requests", "repeat_axis": "Repeat rate", "repeated_lbl": "repeated", "repeated_n": "Repeated requests",
        "matrix_title": "Closure speed vs. repeat rate",
        "matrix_caption": "Each bubble is a request type with at least 30 requests in {p}. Dashed lines are the medians "
                          "for this period. It shows where to look, not why it happens.",
        "x_axis": "Median closure time (hours, log scale)",
        "actions_title": "What each group suggests",
        "actions": {"Effective": ("Fast, rarely repeated", "Keep the current process."),
                    "Root-Cause Attention": ("Fast, but comes back", "Find out why it returns."),
                    "Operational Delay": ("Rarely repeated, but slow", "Shorten the response time."),
                    "Priority Issue": ("Slow and repeated", "Handle first.")},
        "review": "Review first", "issue": "Request type", "group": "Group", "median_col": "Median closure (h)",
        "persistent": "Persistent patterns",
        "persistent_caption": "Needs attention in every period. Not a one-off.",
        "only_one_period": "Persistent patterns need at least two periods of data.",
        "map_title": "Requests by neighborhood",
        "map_caption": "Bubble size: requests. Colour: repeat rate. Positions are approximate neighborhood centers "
                       "from OpenStreetMap. {missing} neighborhoods could not be placed and are listed in the table only.",
        "map_missing": "Neighborhood coordinates are not loaded yet. Run the geocoding step, then dbt build.",
        "top_locations": "Neighborhoods with the most requests",
        "loc_caption": "Neighborhoods only. In Jan – Mar 2026 the source cuts names to the first word, "
                       "so compare neighborhoods within one period.",
        "location": "Neighborhood",
        "rel_title": "How far can these numbers be trusted?",
        "rel_caption": "Every figure here is measured by the data pipeline, not estimated.",
        "rel": [("Without a published status", "From April 2026 the source stopped publishing the status for most requests."),
                ("Closure time without a confirmed status", "A closure time exists, but the status was not published."),
                ("Without a clear neighborhood", "Empty, '0', an unnamed municipality, or a name cut to one word."),
                ("Closure time over 30 days", "Flagged, not deleted. They stay in every count.")],
        "rel_checks": "Checked every time new data arrives",
        "rel_list": ["The file structure is checked against the data contract before anything is loaded.",
                     "Each row's layout is detected from its content, not from the column names.",
                     "No request is lost or duplicated between the raw, cleaned and reporting layers.",
                     "Every request type and neighborhood has a label in both languages, or a warning is raised.",
                     "Every request links to a known date, type, location and status."],
        "groups": {g: g for g in GROUP_ORDER},
        "source": "Source: 940 service requests, Riyadh Municipality open data.",
    },
    "ar": {
        "name": "بَلاغ", "switch": "English",
        "subtitle": "لوحة بيانات تفاعلية لبلاغات البلديات",
        "goal": "الهدف: مساعدة فرق تجربة العميل على اكتشاف البلاغات التي تُغلق ثم تعود، "
                "لمعالجة أسبابها الجذرية وتقليل تكرار الشكاوى.",
        "period": "الفترة", "city": "المدينة: الرياض", "city_hint": "مصممة لأي مدينة، وبيانات الرياض متاحة حاليًا.",
        "tabs": ["نظرة عامة", "أين نتدخل؟", "خريطة الأحياء", "موثوقية البيانات"],
        "steps": ["استُلم", "عولج", "أُغلق", "تكرر؟"],
        "received_sub": "بلاغ", "processed_sub": "نسبة الإنجاز", "processed_np": "الحالة غير منشورة",
        "closed_sub": "وسيط زمن الإغلاق", "repeated_sub": "صُنّفت كمكررة",
        "not_published": "غير منشورة", "hours": "ساعة", "vs": "مقارنة بـ", "pp": "نقطة",
        "summary": "في {p}، <b>{n} نوع بلاغ</b> تُغلق لكنها تعود، أو تتأخر وتتكرر، "
                   "وتمثل معًا <b>{share:.0%} من كل البلاغات</b>.",
        "c_groups": "البلاغات حسب مجموعة المعالجة", "c_domains": "مجالات الخدمة",
        "c_trend": "البلاغات ونسبة التكرار شهريًا", "c_repeated": "أكثر أنواع البلاغات تكرارًا",
        "c_domains_cap": "الرقم: نسبة البلاغات المصنفة كمكررة.",
        "c_repeated_cap": "عدد البلاغات المصنفة كمكررة.",
        "requests": "البلاغات", "repeat_axis": "نسبة التكرار", "repeated_lbl": "مكرر", "repeated_n": "بلاغات مكررة",
        "matrix_title": "سرعة الإغلاق مقابل نسبة التكرار",
        "matrix_caption": "كل دائرة نوع بلاغ له 30 بلاغًا على الأقل في {p}. الخطوط المتقطعة هي الوسيط لهذه الفترة. "
                          "التحليل يحدد أين ننظر، لا لماذا يحدث.",
        "x_axis": "وسيط زمن الإغلاق (ساعات، مقياس لوغاريتمي)",
        "actions_title": "ماذا تقترح كل مجموعة؟",
        "actions": {"Effective": ("سريع ونادر التكرار", "حافظ على الإجراء الحالي."),
                    "Root-Cause Attention": ("سريع لكنه يعود", "ابحث لماذا يتكرر."),
                    "Operational Delay": ("نادر التكرار لكنه بطيء", "قلّل زمن الاستجابة."),
                    "Priority Issue": ("بطيء ومتكرر", "يُعالج أولًا.")},
        "review": "يُراجع أولًا", "issue": "نوع البلاغ", "group": "المجموعة", "median_col": "وسيط الإغلاق (ساعة)",
        "persistent": "أنماط مستمرة",
        "persistent_caption": "تحتاج اهتمامًا في كل الفترات، وليست حالة عابرة.",
        "only_one_period": "الأنماط المستمرة تحتاج بيانات فترتين على الأقل.",
        "map_title": "البلاغات حسب الحي",
        "map_caption": "حجم الدائرة: عدد البلاغات. اللون: نسبة التكرار. المواقع تقريبية لمراكز الأحياء من OpenStreetMap. "
                       "{missing} حيًا لم يُحدد موقعه، ويظهر في الجدول فقط.",
        "map_missing": "إحداثيات الأحياء غير محمّلة بعد. شغّلي خطوة تحديد المواقع ثم dbt build.",
        "top_locations": "الأحياء الأكثر بلاغات",
        "loc_caption": "الأحياء فقط. في فترة يناير – مارس 2026 يقطع المصدر الأسماء على أول كلمة، "
                       "لذا قارني الأحياء داخل الفترة نفسها.",
        "location": "الحي",
        "rel_title": "إلى أي حد يمكن الوثوق بهذه الأرقام؟",
        "rel_caption": "كل رقم هنا يقيسه خط معالجة البيانات، ولا شيء مقدّر.",
        "rel": [("بدون حالة منشورة", "منذ أبريل 2026 توقف المصدر عن نشر حالة أغلب البلاغات."),
                ("زمن إغلاق بدون حالة مؤكدة", "زمن الإغلاق موجود، لكن الحالة غير منشورة."),
                ("بدون حي واضح", "موقع فارغ أو '0' أو بلدية بدون اسم، أو اسم مقطوع على كلمة واحدة."),
                ("زمن إغلاق أكثر من 30 يومًا", "معلّمة وليست محذوفة، وتدخل في كل الأرقام.")],
        "rel_checks": "يُفحص في كل مرة تصل بيانات جديدة",
        "rel_list": ["يُتحقق من شكل الملف مقابل عقد البيانات قبل تحميل أي شيء.",
                     "يُحدد شكل كل صف من محتواه، لا من أسماء الأعمدة.",
                     "لا يضيع أي بلاغ ولا يتكرر بين طبقات البيانات الخام والمنظفة والتقارير.",
                     "لكل نوع بلاغ وحي اسم باللغتين، وإلا يظهر تنبيه.",
                     "كل بلاغ مرتبط بتاريخ ونوع وموقع وحالة معروفة."],
        "groups": {"Effective": "فعّال", "Root-Cause Attention": "يحتاج تحليل السبب الجذري",
                   "Operational Delay": "تأخر تشغيلي", "Priority Issue": "أولوية قصوى"},
        "source": "المصدر: بيانات بلاغات 940 المفتوحة، أمانة منطقة الرياض.",
    },
}

# ---------------------------------------------------------------- language (one clear button, like a website)
if "lang" not in st.session_state:
    st.session_state.lang = "en"


def switch_language():
    st.session_state.lang = "ar" if st.session_state.lang == "en" else "en"


lang = st.session_state.lang
t = T[lang]
rtl = lang == "ar"
issue_col, loc_col, domain_col = ("issue_ar", "location_label_ar", "domain_ar") if rtl else \
                                 ("issue_en", "location_en", "domain_en")


def period_label(codes):
    """['2026Q1', '2026Q2'] -> 'Jan – Jun 2026' / 'يناير – يونيو 2026'."""
    (y1, q1), (y2, q2) = (int(codes[0][:4]), int(codes[0][-1])), (int(codes[-1][:4]), int(codes[-1][-1]))
    start, end = MONTHS[lang][(q1 - 1) * 3], MONTHS[lang][q2 * 3 - 1]
    return f"{start} – {end} {y2}" if y1 == y2 else f"{start} {y1} – {end} {y2}"


def month_label(year_month):
    year, month = year_month.split("-")
    return f"{MONTHS[lang][int(month) - 1]} {year}"


# ---------------------------------------------------------------- data access
@st.cache_resource
def get_client():
    return bigquery.Client(project=PROJECT_ID)


@st.cache_data(ttl=3600, show_spinner=False)
def run_query(sql, quarters=()):
    """Run a query, optionally filtered by quarters. Cached for one hour."""
    params = [bigquery.ArrayQueryParameter("quarters", "STRING", list(quarters))]
    return get_client().query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params)).to_dataframe()


RPT, PERF = f"`{GOLD}.rpt_service_requests`", f"`{GOLD}.gold_issue_performance`"
IN_Q = "source_quarter IN UNNEST(@quarters)"
SQL = {
    "quarters": f"SELECT DISTINCT source_quarter FROM {RPT} ORDER BY 1",
    "kpis": f"""
        WITH base AS (SELECT * FROM {RPT} WHERE {IN_Q}),
        med AS (SELECT ANY_VALUE(m) AS median_closure FROM (
            SELECT PERCENTILE_CONT(closure_hours_kpi, 0.5) OVER () AS m FROM base WHERE closure_hours_kpi IS NOT NULL))
        SELECT COUNT(*) AS total, AVG(is_repeated_int) AS repeat_rate,
               SAFE_DIVIDE(SUM(is_completed_int), SUM(has_published_status)) AS completion,
               SUM(has_published_status) AS with_status, (SELECT median_closure FROM med) AS median_closure
        FROM base""",
    "domains": f"""SELECT domain_ar, domain_en, COUNT(*) AS requests, AVG(is_repeated_int) AS repeat_rate
                   FROM {RPT} WHERE {IN_Q} GROUP BY 1, 2""",
    "matrix": f"""SELECT source_quarter, issue_ar, issue_en, total_requests, repeated_requests, repeat_rate,
                         median_closure_hours, resolution_group, closure_threshold_hours, repeat_threshold
                  FROM {PERF} WHERE {IN_Q}""",
    "persistent": f"""
        SELECT issue_ar, issue_en, SUM(total_requests) AS requests, AVG(repeat_rate) AS repeat_rate
        FROM {PERF} WHERE resolution_group IN ('Root-Cause Attention', 'Priority Issue')
        GROUP BY 1, 2
        HAVING COUNT(DISTINCT source_quarter) = (SELECT COUNT(DISTINCT source_quarter) FROM {PERF})
        ORDER BY requests DESC""",
    "locations": f"""
        SELECT location_label_ar, location_en, ANY_VALUE(lat) AS lat, ANY_VALUE(lon) AS lon,
               COUNT(*) AS requests, AVG(is_repeated_int) AS repeat_rate
        FROM {RPT} WHERE {IN_Q} AND location_type = 'neighborhood' GROUP BY 1, 2""",
    "trend": f"""SELECT year_month, COUNT(*) AS requests, AVG(is_repeated_int) AS repeat_rate
                 FROM {RPT} WHERE {IN_Q} GROUP BY 1 ORDER BY 1""",
    "reliability": f"""
        SELECT COUNT(*) AS total, COUNTIF(status_code = 'not_published') AS no_status,
               COUNTIF(closure_basis = 'closure_value_only') AS closure_only,
               COUNTIF(location_type != 'neighborhood') AS no_neighborhood, COUNTIF(is_closure_outlier) AS outliers
        FROM {RPT} WHERE {IN_Q}""",
}

# ---------------------------------------------------------------- style
SKYLINE = ("<svg viewBox='0 0 400 40' preserveAspectRatio='none' xmlns='http://www.w3.org/2000/svg'><path "
           "fill='%234CAF50' fill-opacity='.10' d='M0 40V14H18V22H36V4H50V22H72V14H94V10H108V22H122V18H136V28H158"
           "V10H180V26H198V14H220V22H238V8H252V18H270V26H284V12H302V20H320V6H338V18H356V24H374V12H392V20H400V40Z'/></svg>")
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;700&display=swap');
html, body, .stApp, button, input, label, [data-testid="stMarkdownContainer"] {{
    font-family: 'IBM Plex Sans Arabic', 'Segoe UI', sans-serif; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stSidebarCollapsedControl"] {{ display: none; }}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.5rem; max-width: 1240px; }}
{".stMainBlockContainer { direction: rtl; text-align: right; }" if rtl else ""}
.logo {{ color: {GOLDEN}; font-size: 2.8rem; font-weight: 700; line-height: 1.1; margin: 0; }}
.subtitle {{ color: {TEXT}; font-size: 1.2rem; font-weight: 500; margin: .35rem 0 0; }}
.goal {{ color: {MUTED}; font-size: 1rem; margin: .6rem 0 1.2rem; max-width: 70ch; line-height: 1.7; }}
.city {{ display: inline-block; border: 1px solid {LINE}; border-radius: 999px; padding: .35rem .9rem;
    color: {TEXT}; font-size: .9rem; margin-top: 1.9rem; }}
.hero {{ position: relative; padding: 1.5rem 0 3rem; }}
.hero::after {{ content: ""; position: absolute; inset: auto 0 0 0; height: 46px;
    background: url("data:image/svg+xml;utf8,{SKYLINE}") bottom / 100% 100% no-repeat; pointer-events: none; }}
.journey {{ display: grid; grid-template-columns: repeat(4, 1fr); position: relative; }}
.journey::before {{ content: ""; position: absolute; top: 22px; inset-inline: 12.5%; height: 2px; background: {LINE}; }}
.step {{ text-align: center; position: relative; padding: 0 .5rem; }}
.dot {{ width: 44px; height: 44px; border-radius: 50%; margin: 0 auto .9rem; display: grid; place-items: center;
    background: {GOLDEN}; color: {NAVY}; font-weight: 700; font-size: 1.1rem; position: relative; }}
.step .name {{ color: {GOLDEN}; font-weight: 700; font-size: 1.05rem; }}
.step .value {{ color: {TEXT}; font-weight: 700; font-size: 2.2rem; line-height: 1.2; margin-top: .2rem; }}
.step .value.small {{ font-size: 1.3rem; padding: .55rem 0; color: {MUTED}; }}
.step .sub {{ color: {MUTED}; font-size: .9rem; }}
.step .delta {{ font-size: .85rem; margin-top: .3rem; color: {MUTED}; }}
.step .delta.good {{ color: {GREEN}; }} .step .delta.bad {{ color: {RED}; }}
.step.focus .dot {{ background: transparent; border: 2px solid {GOLDEN}; color: {GOLDEN}; }}
.step.focus .value {{ color: {GOLDEN}; }}
.summary {{ border-inline-start: 4px solid {GOLDEN}; background: {PANEL}; padding: 1rem 1.25rem;
    border-radius: 6px; margin: .5rem 0 1.5rem; font-size: 1.05rem; color: {TEXT}; }}
.summary b {{ color: {GOLDEN}; }}
.actions {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: .5rem 0 1.5rem; }}
.action {{ border-top: 3px solid; padding: .8rem .2rem 0; }}
.action .g {{ font-weight: 700; color: {TEXT}; }} .action .m {{ color: {MUTED}; font-size: .9rem; margin: .2rem 0; }}
.action .do {{ color: {TEXT}; }}
.src {{ color: {MUTED}; font-size: .8rem; margin-top: 2.5rem; }}
[data-testid="stTabs"] button p {{ font-size: 1rem; }}
@media (max-width: 760px) {{ .journey, .actions {{ grid-template-columns: repeat(2, 1fr); row-gap: 1.5rem; }}
    .journey::before {{ display: none; }} }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- header
head, switch = st.columns([5, 1])
with switch:
    st.button(t["switch"], on_click=switch_language, use_container_width=True)
with head:
    st.html(f'<p class="logo">{t["name"]}</p><p class="subtitle">{t["subtitle"]}</p><p class="goal">{t["goal"]}</p>')

all_q = run_query(SQL["quarters"]).source_quarter.tolist()
period_col, city_col = st.columns([4, 1])
with period_col:
    choice = st.radio(t["period"], ["ALL"] + all_q[::-1], horizontal=True, key="period",
                      format_func=lambda c: period_label(all_q) if c == "ALL" else period_label([c]))
with city_col:
    st.html(f'<span class="city" title="{t["city_hint"]}">📍 {t["city"]}</span>')

selected = all_q if choice == "ALL" else [choice]
previous = all_q[all_q.index(choice) - 1] if choice in all_q and all_q.index(choice) > 0 else None
period_now = period_label(selected)
period_prev = period_label([previous]) if previous else None

# ---------------------------------------------------------------- the request journey
k = run_query(SQL["kpis"], tuple(selected)).iloc[0]
p = run_query(SQL["kpis"], (previous,)).iloc[0] if previous else None
published = bool(k.total) and k.with_status / k.total >= 0.05


def delta(now, before, fmt, lower_is_better=True):
    if before is None:
        return ""
    diff = now - before
    cls = "" if abs(diff) < 1e-9 else ("good" if (diff < 0) == lower_is_better else "bad")
    return f'<div class="delta {cls}">{fmt(diff)} {t["vs"]} {period_prev}</div>'


steps = [
    ("", f"{int(k.total):,}", t["received_sub"],
     f'<div class="delta">{(k.total / p.total - 1):+.0%} {t["vs"]} {period_prev}</div>' if p is not None else ""),
    ("", f"{k.completion:.1%}" if published else t["not_published"],
     t["processed_sub"] if published else t["processed_np"], ""),
    ("", f"{k.median_closure:.0f} {t['hours']}", t["closed_sub"],
     delta(k.median_closure, p.median_closure if p is not None else None, lambda d: f"{d:+.0f} {t['hours']}")),
    ("focus", f"{k.repeat_rate:.1%}", t["repeated_sub"],
     delta(k.repeat_rate, p.repeat_rate if p is not None else None, lambda d: f"{d * 100:+.1f} {t['pp']}")),
]
journey = "".join(
    f'<div class="step {cls}"><div class="dot">{"?" if cls else i + 1}</div><div class="name">{t["steps"][i]}</div>'
    f'<div class="value{" small" if (i == 1 and not published) else ""}">{value}</div><div class="sub">{sub}</div>{d}</div>'
    for i, (cls, value, sub, d) in enumerate(steps))
st.html(f'<div class="hero"><div class="journey">{journey}</div></div>')


# ---------------------------------------------------------------- chart helpers
def style_fig(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="IBM Plex Sans Arabic, Segoe UI, sans-serif", color=TEXT, size=13),
                      legend=dict(orientation="h", y=-0.15, title=None), coloraxis_showscale=False)
    fig.update_xaxes(gridcolor=LINE, zeroline=False, autorange="reversed" if rtl else None)
    fig.update_yaxes(gridcolor=LINE, zeroline=False, side="right" if rtl else "left")
    return fig


def ranked_bars(df, label_col, value_col, text, height, color="repeat_rate"):
    df = df.sort_values(value_col)
    fig = px.bar(df, x=value_col, y=label_col, orientation="h", color=color,
                 color_continuous_scale=[[0, BLUE], [1, GOLDEN]], text=text(df),
                 labels={value_col: "", label_col: ""}, hover_data={value_col: ":,", color: ":.1%"})
    fig.update_traces(textposition="inside", insidetextanchor="start" if rtl else "end",
                      textfont=dict(color=NAVY, size=12))
    return style_fig(fig, height)


m = run_query(SQL["matrix"], tuple(selected))
flagged = m[m.resolution_group.isin(["Root-Cause Attention", "Priority Issue"])]
share = flagged.total_requests.sum() / m.total_requests.sum()
pct_col = lambda label: st.column_config.ProgressColumn(label, min_value=0, max_value=100, format="%.0f%%")

tab_overview, tab_act, tab_map, tab_trust = st.tabs(t["tabs"])

# ---------------------------------------------------------------- 1. overview: four charts
with tab_overview:
    st.html(f'<div class="summary">{t["summary"].format(p=period_now, n=flagged.issue_en.nunique(), share=share)}</div>')
    a, b = st.columns(2, gap="large")
    with a:
        st.subheader(t["c_groups"])
        g = (m[m.resolution_group != "Insufficient data"].groupby("resolution_group", as_index=False).total_requests.sum()
             .assign(label=lambda x: x.resolution_group.map(t["groups"])))
        fig = px.pie(g, names="label", values="total_requests", hole=0.62, color="label",
                     color_discrete_map={t["groups"][k_]: c for k_, c in GROUP_COLORS.items()},
                     category_orders={"label": [t["groups"][k_] for k_ in GROUP_ORDER]})
        fig.update_traces(textinfo="percent", textfont=dict(color=NAVY, size=13), sort=False,
                          marker=dict(line=dict(color=NAVY, width=2)))
        st.plotly_chart(style_fig(fig, 380))
    with b:
        st.subheader(t["c_domains"])
        st.caption(t["c_domains_cap"])
        d = run_query(SQL["domains"], tuple(selected))
        st.plotly_chart(ranked_bars(d, domain_col, "requests",
                                    lambda x: x.repeat_rate.map(lambda r: f"{r:.0%} {t['repeated_lbl']}"), 360))
    c, e = st.columns(2, gap="large")
    with c:
        st.subheader(t["c_trend"])
        tr = run_query(SQL["trend"], tuple(selected)).assign(month=lambda x: x.year_month.map(month_label))
        fig = go.Figure()
        fig.add_bar(x=tr.month, y=tr.requests, name=t["requests"], marker_color=BLUE)
        fig.add_scatter(x=tr.month, y=tr.repeat_rate, name=t["repeat_axis"], yaxis="y2",
                        mode="lines+markers", line=dict(color=GOLDEN, width=3))
        fig = style_fig(fig, 380)
        fig.update_layout(yaxis2=dict(overlaying="y", side="left" if rtl else "right",   # after style_fig,
                                      tickformat=".0%", range=[0, 1], showgrid=False))  # so it keeps its own side
        st.plotly_chart(fig)
    with e:
        st.subheader(t["c_repeated"])
        st.caption(t["c_repeated_cap"])
        top = (m.groupby(["issue_ar", "issue_en"], as_index=False)
                .agg(repeated_requests=("repeated_requests", "sum"), total_requests=("total_requests", "sum"))
                .assign(repeat_rate=lambda x: x.repeated_requests / x.total_requests)
                .nlargest(8, "repeated_requests"))
        st.plotly_chart(ranked_bars(top, issue_col, "repeated_requests",
                                    lambda x: x.repeated_requests.map(lambda v: f"{int(v):,}"), 360))

# ---------------------------------------------------------------- 2. where to act
with tab_act:
    focus_q = selected[-1]
    mq = m[m.source_quarter == focus_q]
    st.subheader(t["matrix_title"])
    st.caption(t["matrix_caption"].format(p=period_label([focus_q])))
    plot_df = mq[mq.resolution_group != "Insufficient data"].copy()
    plot_df["x"] = plot_df.median_closure_hours.clip(lower=0.5)        # log scale cannot show 0
    plot_df["group_label"] = plot_df.resolution_group.map(t["groups"])
    fig = px.scatter(plot_df, x="x", y="repeat_rate", size="total_requests", color="group_label",
                     color_discrete_map={t["groups"][k_]: c for k_, c in GROUP_COLORS.items()},
                     category_orders={"group_label": [t["groups"][k_] for k_ in GROUP_ORDER]},
                     hover_name=issue_col, log_x=True, size_max=48,
                     hover_data={"x": False, "group_label": False, "total_requests": ":,",
                                 "median_closure_hours": ":.0f", "repeat_rate": ":.1%"},
                     labels={"x": t["x_axis"], "repeat_rate": t["repeat_axis"], "total_requests": t["requests"],
                             "median_closure_hours": t["median_col"], "group_label": ""})
    fig.add_vline(x=plot_df.closure_threshold_hours.iloc[0], line_dash="dash", line_color=MUTED)
    fig.add_hline(y=plot_df.repeat_threshold.iloc[0], line_dash="dash", line_color=MUTED)
    fig.update_traces(marker=dict(line=dict(width=0.5, color=NAVY), opacity=0.88))
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(style_fig(fig, 520))

    st.subheader(t["actions_title"])
    st.html('<div class="actions">' + "".join(
        f'<div class="action" style="border-color:{GROUP_COLORS[g_]}"><div class="g">{t["groups"][g_]}</div>'
        f'<div class="m">{t["actions"][g_][0]}</div><div class="do">{t["actions"][g_][1]}</div></div>'
        for g_ in GROUP_ORDER) + "</div>")

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"**{t['review']}**")
        review = (mq[mq.resolution_group.isin(["Root-Cause Attention", "Priority Issue"])]
                  .nlargest(10, "total_requests")
                  .assign(group=lambda x: x.resolution_group.map(t["groups"]), repeat_pct=lambda x: x.repeat_rate * 100))
        st.dataframe(review[[issue_col, "group", "total_requests", "median_closure_hours", "repeat_pct"]],
                     hide_index=True, column_config={
                         issue_col: t["issue"], "group": t["group"],
                         "total_requests": st.column_config.NumberColumn(t["requests"], format="%d"),
                         "median_closure_hours": st.column_config.NumberColumn(t["median_col"], format="%.0f"),
                         "repeat_pct": pct_col(t["repeat_axis"])})
    with right:
        st.markdown(f"**{t['persistent']}**")
        st.caption(t["persistent_caption"])
        if len(all_q) < 2:
            st.info(t["only_one_period"])
        else:
            pers = run_query(SQL["persistent"]).assign(repeat_pct=lambda x: x.repeat_rate * 100)
            st.dataframe(pers[[issue_col, "requests", "repeat_pct"]], hide_index=True, column_config={
                issue_col: t["issue"], "requests": st.column_config.NumberColumn(t["requests"], format="%d"),
                "repeat_pct": pct_col(t["repeat_axis"])})

# ---------------------------------------------------------------- 3. neighborhood map
with tab_map:
    loc = run_query(SQL["locations"], tuple(selected))
    placed = loc.dropna(subset=["lat", "lon"])
    st.subheader(t["map_title"])
    if placed.empty:
        st.info(t["map_missing"])
    else:
        st.caption(t["map_caption"].format(missing=len(loc) - len(placed)))
        fig = px.scatter_map(placed, lat="lat", lon="lon", size="requests", color="repeat_rate",
                             color_continuous_scale=[[0, BLUE], [1, GOLDEN]], hover_name=loc_col,
                             hover_data={"lat": False, "lon": False, "requests": ":,", "repeat_rate": ":.1%"},
                             labels={"requests": t["requests"], "repeat_rate": t["repeat_axis"]},
                             size_max=34, zoom=9.6, center=dict(lat=24.72, lon=46.68), map_style="carto-darkmatter")
        fig.update_layout(height=560, margin=dict(l=0, r=0, t=0, b=0), coloraxis_showscale=False,
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)
    st.subheader(t["top_locations"])
    st.caption(t["loc_caption"])
    st.plotly_chart(ranked_bars(loc.nlargest(15, "requests"), loc_col, "requests",
                                lambda x: x.repeat_rate.map(lambda r: f"{r:.0%} {t['repeated_lbl']}"), 520))

# ---------------------------------------------------------------- 4. data reliability
with tab_trust:
    st.subheader(t["rel_title"])
    st.caption(t["rel_caption"])
    r = run_query(SQL["reliability"], tuple(selected)).iloc[0]
    values = [f"{r.no_status / r.total:.1%}", f"{r.closure_only / r.total:.1%}",
              f"{r.no_neighborhood / r.total:.1%}", f"{int(r.outliers):,}"]
    for column, (label, help_text), value in zip(st.columns(4), t["rel"], values):
        column.metric(label, value, help=help_text)
    st.markdown(f"**{t['rel_checks']}**")
    st.markdown("\n".join(f"- {line}" for line in t["rel_list"]))

st.html(f'<p class="src">{t["source"]}</p>')
