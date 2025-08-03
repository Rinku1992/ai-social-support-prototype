def recommend_enablement(app_data):
    if app_data.income < 15000:
        return "Job Counseling, Upskilling Program A"
    return "Training Program B"
