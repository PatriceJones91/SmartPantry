import streamlit as st


def apply_smart_pantry_theme():
    st.markdown(
        """
        <style>
        :root {
            --sp-green: #1f7a3f;
            --sp-dark-green: #14532d;
            --sp-orange: #f97316;
            --sp-soft-orange: #fff0df;
            --sp-blue: #2563eb;
            --sp-baby-blue: #d9f2ff;
            --sp-cream: #fffaf2;
            --sp-card: #ffffff;
        }

        .stApp {
            background: linear-gradient(135deg, #eef8ff 0%, #d9f2ff 28%, #f6fff3 68%, #e8ffe8 100%);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #14532d 0%, #1f7a3f 70%, #2563eb 100%);
        }

        section[data-testid="stSidebar"] * {
            color: white !important;
        }

        h1, h2, h3 {
            color: var(--sp-dark-green);
        }

        div.stButton > button,
        div.stDownloadButton > button {
            background-color: var(--sp-green);
            color: white;
            border-radius: 12px;
            border: 2px solid var(--sp-green);
            font-weight: 700;
        }

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {
            background-color: var(--sp-orange);
            color: white;
            border: 2px solid var(--sp-orange);
        }

        .smart-card {
            background: var(--sp-card);
            border: 1px solid #dcebd6;
            border-left: 7px solid var(--sp-green);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
        }

        .smart-card-orange {
            border-left-color: var(--sp-orange);
        }

        .smart-card-blue {
            border-left-color: var(--sp-blue);
        }

        .friendly-note {
            background: #ffffff;
            border: 1px solid #dcebd6;
            border-left: 7px solid var(--sp-green);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
            box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .alert-red {
            background: #ffe5e5;
            border: 2px solid #dc2626;
            border-left: 10px solid #dc2626;
            color: #7f1d1d;
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 12px;
            font-weight: 700;
        }

        .alert-orange {
            background: #ffedd5;
            border: 2px solid #f97316;
            border-left: 10px solid #f97316;
            color: #7c2d12;
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 12px;
            font-weight: 700;
        }

        .alert-blue {
            background: #d9f2ff;
            border: 2px solid #60a5fa;
            border-left: 10px solid #60a5fa;
            color: #0f3f66;
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 12px;
            font-weight: 700;
        }

        .history-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
            border: 1px solid #e5e7eb;
        }

        .history-green { border-left: 10px solid #22c55e; }
        .history-purple { border-left: 10px solid #a855f7; }
        .history-brown { border-left: 10px solid #a16207; }
        .history-red { border-left: 10px solid #ef4444; }
        .history-blue { border-left: 10px solid #3b82f6; }
        .history-gray { border-left: 10px solid #9ca3af; }

        .grocery-list-card {
            background: #ffffff;
            border: 1px solid #dcebd6;
            border-left: 7px solid #1f7a3f;
            border-radius: 18px;
            padding: 18px 22px;
            margin-bottom: 16px;
            box-shadow: 0 6px 18px rgba(20, 83, 45, 0.08);
        }

        .grocery-list-high { border-left-color: #ef4444; }
        .grocery-list-medium { border-left-color: #f97316; }
        .grocery-list-low { border-left-color: #2563eb; }
        .grocery-list-manual { border-left-color: #a855f7; }

        .small-note {
            color: #355c3a;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )