def calculate_risk(data, user_history):
    score = 0
    reasons = []

    # Safely parse login time with error handling
    try:
        hour = int(data["login_time"].split(":")[0])
    except (ValueError, IndexError, AttributeError):
        # If login_time is invalid, default to safe hour (9 AM)
        hour = 9
        reasons.append("Invalid login time format")

    downloads = data.get("downloads", 0)
    location = data.get("location", "Unknown")
    failed_attempts = data.get("failed_attempts", 0)

    # If no history → early stage user
    if len(user_history) < 3:
        if hour < 6 or hour > 22:
            score += 20
            reasons.append("Login outside standard working hours")

        if downloads > 10:
            score += 30
            reasons.append("High download volume")

        if failed_attempts > 3:
            score += 20
            reasons.append("Multiple failed login attempts")

        return score, reasons

    # ---- Build Baseline ----
    # Safely calculate average login hour
    valid_hours = []
    for log in user_history:
        try:
            valid_hours.append(int(log["login_time"].split(":")[0]))
        except (ValueError, IndexError, AttributeError, KeyError):
            continue  # Skip invalid entries

    avg_login_hour = sum(valid_hours) / len(valid_hours) if valid_hours else 9

    avg_downloads = (
        sum(log.get("downloads", 0) for log in user_history) / len(user_history)
        if user_history
        else 0
    )

    common_locations = {}
    for log in user_history:
        loc = log.get("location", "Unknown")
        common_locations[loc] = common_locations.get(loc, 0) + 1

    usual_location = max(common_locations, key=common_locations.get)

    # ---- Deviation Detection ----

    # Login time deviation
    if abs(hour - avg_login_hour) > 3:
        score += 25
        reasons.append("Login time deviates from normal behavior")

    # Download deviation
    if downloads > avg_downloads * 2:
        score += 35
        reasons.append("Download activity significantly higher than baseline")

    # Location anomaly
    if location != usual_location:
        score += 25
        reasons.append("Login from unusual location")

    # Failed attempts
    if failed_attempts > 3:
        score += 15
        reasons.append("Multiple failed login attempts")

    return score, reasons
