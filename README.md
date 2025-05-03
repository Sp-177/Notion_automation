# 🧠 Notion Automation with AWS Lambda (NOTION AUTOMATION AAWS)

This project automates a task related to Notion using AWS Lambda. It runs **once per day** automatically using an **EventBridge (CloudWatch Events)** trigger and is optimized to run within the AWS Free Tier.

---

## 📌 Features

- ⏰ Daily scheduled execution using EventBridge
- ⚙️ AWS Lambda function with minimal execution cost
- 🔍 Logs and monitoring via CloudWatch
- ✅ Tested and deployed in production

---

## 🧱 Architecture

- **AWS Lambda** – Core function that performs the automation
- **EventBridge Rule** – Triggers the Lambda once per day
- **CloudWatch Logs** – Stores execution logs
- **(Optional)** SNS – Sends alerts if something fails

---

## 🚀 Deployment Steps

1. **Write your Lambda function** in Python/Node.js
2. **Deploy it via AWS Console or AWS CLI**
3. **Add a trigger**:
   - Use EventBridge (CloudWatch Events)
   - Cron expression for once per day: `cron(0 9 * * ? *)` (runs daily at 9 AM UTC)
4. **Test the function** via the Lambda Console
5. **Verify execution** in:


---

## ✅ Free Tier Usage

- **Execution Time**: 1 minute/day
- **Estimated Monthly Usage**: ~225 GB-seconds (within the free 400,000 GB-sec/month)
- **Monthly Invocations**: 30 (well under 1 million free requests)

---

## 📈 Monitoring

- CloudWatch logs enabled by default
- Optional monitoring:
- Create **CloudWatch Alarms** for Lambda errors
- Configure **SNS Notifications** for failure alerts

---

## 📂 Project Structure

├── lambda_function.py # Main Lambda code
├── README.md # Project documentation
└── requirements.txt # (Optional) Dependencies if using Python


---

## 📬 Contact

For improvements or support, feel free to fork the repo, raise an issue, or contribute via pull requests.

---
