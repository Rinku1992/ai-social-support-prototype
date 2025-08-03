def predict_eligibility(app_data):
    if app_data.income < 20000 and not app_data.credit_report.defaults:
        return "Approved"
    return "Soft Declined"
