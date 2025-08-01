import requests
import pandas as pd
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Logging config
logging.basicConfig(level=logging.INFO)

pd.set_option('display.max_columns', None)

# Email function
def send_email(subject, body, receiver_email="sakaria2608@gmail.com"):
    sender_email = "sakariajasus11@gmail.com"
    password = "cktd xdza bbiw cthn"  # Use env variable in production

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Main logic
try:
    url = "https://api.github.com/repos/squareshift/stock_analysis/contents/"
    response = requests.get(url)
    response.raise_for_status()

    files = response.json()
    csv_files = [file["download_url"] for file in files if file["name"].endswith(".csv")]
    #print(csv_files)

    metadata_url = csv_files.pop()
    metadata_df = pd.read_csv(metadata_url)
    #print(metadata_df)

    dataframes = []
    for url in csv_files:
        try:
            file_name = url.split("/")[-1].replace(".csv", "")
            df = pd.read_csv(url)
            df["Symbol"] = file_name
            dataframes.append(df)
        except Exception as e:
            logging.warning(f"Failed to read {url}: {e}")

    combined_df = pd.concat(dataframes, ignore_index=True)
    merged_df = pd.merge(combined_df, metadata_df, on="Symbol", how="left")

    # Aggregation
    result = merged_df.groupby("Sector").agg({
        'open': 'mean',
        'close': 'mean',
        'high': 'max',
        'low': 'min',
        'volume': 'mean'
    }).reset_index()

    merged_df["timestamp"] = pd.to_datetime(merged_df["timestamp"])
    filtered_df = merged_df[
        (merged_df["timestamp"] >= "2021-01-01") & 
        (merged_df["timestamp"] <= "2021-05-26")
    ]

    result_time = filtered_df.groupby("Sector").agg({
        'open': 'mean',
        'close': 'mean',
        'high': 'max',
        'low': 'min',
        'volume': 'mean'
    }).reset_index()

    list_sector = ["TECHNOLOGY", "FINANCE"]
    final_df = result_time[result_time["Sector"].isin(list_sector)].reset_index(drop=True)

    print("Filtered Sector Analysis:\n", final_df)

    # Send success email
    subject = "Lambda Function Executed Successfully"
    body = f"Stock analysis script ran successfully.\n\nFiltered Result:\n{final_df.to_string(index=False)}"
    send_email(subject, body)

except Exception as e:
    error_message = str(e)
    logging.error(f"Lambda function error: {error_message}")
    send_email("Lambda Function Error", f"An error occurred:\n\n{error_message}")