from fasthtml.common import *
from dataclasses import dataclass
import re  # For email validation
from datetime import datetime  # For getting the current date and time
import toml #to access screts.toml file for passwords
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

#load config
config = toml.load("secrets.toml")

#ionos smtp password
password = config['secrets']['ionos_password']

today = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

# Initialize the FastHTML app and SQLite database
app, rt = fast_app(
    hdrs=(Style("""
        .error {
            border: 2px solid red;
        }
    """),)
)
db = Database("submissions.db")

# Email sending function
def send_email(data: dict):
    msg = MIMEMultipart()
    msg['From'] = 'admin@samcresearchforum.org'
    msg['To'] = data['email']
    msg['Subject'] = 'Scholarly Activity Submission'
    body = f"Dear {data['full_name'].title()}, \n\nYour submission for {data['research_type']} with the following description:\n\nSubmit Date: {today}\nDepartment: {data['dept']}\nDescription: {data['description']}\nSubmit to Research Forum: {data['post_forum'] == 'on'}\n\nThank you for your submission. Please let us know if you have any questions. \n\nSincerely,\nSAMC Research Committee"
    msg.attach(MIMEText(body, 'plain'))

    # Prepare email receipents
    recipients = [data['email']]+['phillip.kim@samc.com']

    # Send the email
    server = smtplib.SMTP('smtp.ionos.com', 587)
    server.starttls()
    server.login('admin@samcresearchforum.org', password)
    text = msg.as_string()
    server.sendmail('admin@samcresearchforum.org', recipients, text)
    server.quit()


@dataclass
class FormSubmission:
    id: int #auto incremented
    date: str
    full_name: str
    title: str
    dept: str
    research_type: str
    email: str
    description: str
    post_forum: bool = False  # Default to False since it's optional

# Create a table in SQLite
submissions_table = db.create(FormSubmission, pk="id")

# Define a helper function to validate email
def is_valid_email(email):
    # Simple email validation (can be enhanced with more robust regex)
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Define the form page
@rt("/")
def form_view():
    return Titled("SAMC Scholarly Activity Submission Form", 
        Form(method="post", action="/submit")(
            Fieldset(
                Label("Full Name", Input(type="text", name="full_name", required=True, placeholder="Enter your full name")),
                Label("Select Your Title", 
                      Select(name="title", required=True)(
                          Option(value="")("Select Your Title", Selected=False),
                          Option(value="Faculty")("Faculty"),
                          Option(value="Resident")("Resident"),
                          Option(value="Student")("Student"),
                          Option(value="Staff")("Staff"),
                          Option(value="Other")("Other"),
                      )),
                Label("Department", 
                       Select(name="dept", required=True)(
                            Option(value="")("Select Your Department", Selected=False),
                            Option(value="Emergency Medicine")("Emergency Medicine"),
                            Option(value="Family Medicine")("Family Medicine"),
                            Option(value="Internal Medicine")("Internal Medicine"),
                            Option(value="OB/GYN")("OB/GYN"),
                            Option(value="Surgery")("Surgery"),
                            Option(value="Other")("Other"),
                        )),
                Label("Research Type",
                    Select(name="research_type", required=True)(
                        Option(value="")("Select Research Type", Selected=False),
                        Option(value="Abstract for Conferences")("Abstract for Conferences"),
                        Option(value="Case Reports")("Case Reports"),
                        Option(value="Prosepective Studies")("Prosepective Studies"),
                        Option(value="Retrospective Studies")("Retrospective Studies"),
                        Option(value="QI/PI")("QI/PI"),
                        Option(value="Other")("Other"),
                    )),
                Label("Email", Input(type="email", name="email", required=True, placeholder="Enter your email")),
                Label("Description", Textarea(name="description", required=True, placeholder="Provide a brief description")),
                Label(Input(type="checkbox", name="post_forum"), "Post to SAMC Research Forum")  # Optional checkbox
            ),
            Button(type="submit")("Submit")
        )
    )

# Handle form submission
@rt("/submit")
async def post(req):
    form_data = await req.form()  # Await the form data

    # Check for missing required fields
    missing_fields = [key for key in ["full_name", "title", "email", "description"] if not form_data.get(key)]

    # Email validation
    email = form_data.get("email")
    if email and not is_valid_email(email):
        missing_fields.append("email")  # Add email to missing fields if invalid

    if missing_fields:
        # Re-render the form with previous data, highlighting missing fields in red
        return Titled("Submit Form - Error", 
            P("Please fill out all required fields or correct errors."),
            Form(method="post", action="/submit")(
                Fieldset(
                    Label("Full Name", Input(type="text", name="full_name", value=form_data.get('full_name', ""), required=True, placeholder="Enter your full name", cls="error" if "full_name" in missing_fields else "")),
                    Label("Select Your Title", 
                          Select(name="title", required=True, cls="error" if "title" in missing_fields else "")(
                              Option(value="")("Select Your Title"),
                              Option(value="Faculty", selected=form_data.get('title') == "Faculty")("Faculty"),
                              Option(value="Resident", selected=form_data.get('title') == "Resident")("Resident"),
                              Option(value="Student", selected=form_data.get('title') == "Student")("Student"),
                              Option(value="Staff", selected=form_data.get('title') == "Staff")("Staff"),
                              Option(value="Other", selected=form_data.get('title') == "Other")("Other"),
                          )),
                    Label("Select Your Department",
                          Select(name="dept", required=True, cls="error" if "dept" in missing_fields else "")(
                              Option(value="")("Select Your Department"),
                              Option(value="Emergency Medicine", selected=form_data.get('dept') == "Emergency Medicine")("Emergency Medicine"),
                              Option(value="Family Medicine", selected=form_data.get('dept') == "Family Medicine")("Family Medicine"),
                              Option(value="Internal Medicine", selected=form_data.get('dept') == "Internal Medicine")("Internal Medicine"),
                              Option(value="OB/GYN", selected=form_data.get('dept') == "OB/GYN")("OB/GYN"),
                              Option(value="Surgery", selected=form_data.get('dept') == "Surgery")("Surgery"),
                              Option(value="Other", selected=form_data.get('dept') == "Other")("Other"),
                          )),
                    Label("Research Type",
                          Select(name="research_type", required=True, cls="error" if "research_type" in missing_fields else "")(
                              Option(value="")("Select Research Type"),
                              Option(value="Abstract for Conferences", selected=form_data.get('research_type') == "Abstract for Conferences")("Abstract for Conferences"),
                              Option(value="Case Reports", selected=form_data.get('research_type') == "Case Reports")("Case Reports"),
                              Option(value="Prosepective Studies", selected=form_data.get('research_type') == "Prosepective Studies")("Prosepective Studies"),
                              Option(value="Retrospective Studies", selected=form_data.get('research_type') == "Retrospective Studies")("Retrospective Studies"),
                              Option(value="QI/PI", selected=form_data.get('research_type') == "QI/PI")("QI/PI"),
                              Option(value="Other", selected=form_data.get('research_type') == "Other")("Other"),
                          )),
                    Label("Email", Input(type="email", name="email", value=form_data.get('email', ""), required=True, placeholder="Enter your email", cls="error" if "email" in missing_fields else "")),
                    Label("Description", Textarea(name="description", required=True, placeholder="Provide a brief description", cls="error" if "description" in missing_fields else "")(form_data.get('description', ""))),
                    Label(Input(type="checkbox", name="post_forum", checked="post_forum" in form_data), "Post to SAMC Research Forum")  # Optional checkbox
                ),
                Button(type="submit")("Submit")
            )
        )
    else:
        # Save form data to the database (post_forum is optional and defaults to False)
        submission = FormSubmission(
            date=today,
            full_name=form_data["full_name"],
            title=form_data["title"],
            dept=form_data["dept"],
            research_type=form_data["research_type"],
            email=form_data["email"],
            description=form_data["description"],
            post_forum=form_data.get("post_forum", False)  # Handle checkbox being optional
        )
        submissions_table.insert(submission)
        # Send email to the user and static email address
        send_email({"full_name": form_data["full_name"], "title": form_data["title"], "dept": form_data["dept"], "research_type": form_data["research_type"], "email": form_data["email"], "description": form_data["description"], "post_forum": form_data.get("post_forum", False)})   

        # Show confirmation and link to submit another form
        return Titled("Form Submitted", 
            P("Your form has been successfully submitted!"),
            A(href="/")("Submit another form")
        )

# Run the server
serve()