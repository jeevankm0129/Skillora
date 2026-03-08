from utils.email_sender import send_email

success = send_email(
    to_email="jeevansharath4@gmail.com",  # put your email here
    subject="Skillora Test Email",
    body="If you received this, your email sender is working perfectly.",
)

print("Email sent?", success)
