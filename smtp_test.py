import smtplib

smtp_server = "smtp.office365.com"
port = 587

username = "vishnu.srivastava@apvtechnologies.com"
password = "YOUR_APP_PASSWORD"

server = smtplib.SMTP(smtp_server, port)
server.starttls()

server.login(username, password)

print("SMTP LOGIN SUCCESS")

server.quit()