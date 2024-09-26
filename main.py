from fasthtml.common import *
from dataclasses import dataclass
import re  # For email validation
from datetime import datetime  # For getting the current date and time
import os # get environment variables
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL_RC")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY_RC")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#ionos smtp password
password = os.environ.get('EMAIL_PASSWORD')


today = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

# Initialize the FastHTML app
app, rt = fast_app(
    hdrs=(Style("""
        .error {
            border: 2px solid red;
        }
    """),
    Link(rel="icon", type="image/x-icon", href="assets/favicon.ico"), # Updated path
    Link(rel="icon", type="image/png", sizes="32x32", href="assets/favicon-32x32.png"),
    Link(rel="icon", type="image/png", sizes="16x16", href="assets/favicon-16x16.png"),
    Link(rel="apple-touch-icon", sizes="180x180", href="assets/apple-touch-icon.png"),
    Link(rel="icon", sizes="192x192", href="assets/android-chrome-192x192.png"),
    Link(rel="icon", sizes="512x512", href="assets/android-chrome-512x512.png")
    )
)

# Email sending function
def send_email(data: dict):
    msg = MIMEMultipart()
    msg['From'] = 'admin@samcresearchforum.org'
    msg['To'] = data['email']
    msg['Subject'] = 'Scholarly Activity Submission'
    body = f"Dear {data['full_name'].title()}, \nYour submission for {data['research_type']} with the following description:\n\nSubmit Date: {today}\nDepartment: {data['dept']}\nDescription: {data['description']}\nSubmit to Research Forum: {data['post_forum'] == 'on'}\n\nThank you for your submission. Please let us know if you have any questions. \nSincerely,\nSAMC Research Committee"
    msg.attach(MIMEText(body, 'plain'))

    # Prepare email recipients
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
    id: int  # auto incremented
    #date: str
    full_name: str
    title: str
    dept: str
    research_type: str
    email: str
    description: str
    post_forum: bool = False  # Default to False since it's optional

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
        # Save form data to Supabase
        submission = {
            "full_name": form_data["full_name"],
            "title": form_data["title"],
            "dept": form_data["dept"],
            "research_type": form_data["research_type"],
            "email": form_data["email"],
            "description": form_data["description"],
            "post_forum": "post_forum" in form_data  # Handle checkbox being optional
        }
        
       # Insert data into Supabase
        response = supabase.table("researchform").insert(submission).execute()

        # Handle response
        if response.data:
            # Extract the submitted data
            submitted_data = response.data[0]  # Since it's a list with one item, we access the first element

            # Form submission successful
            # send_email({"full_name": form_data["full_name"], "title": form_data["title"], "dept": form_data["dept"], "research_type": form_data["research_type"], "email": form_data["email"], "description": form_data["description"], "post_forum": "post_forum" in form_data})   
             # Send email to the user and static email address
            return Titled("Form Submitted", 
                P("Your form has been successfully submitted!"),
                Ul(*[
                    Li(f"Submitted ID: {submitted_data['id']}"),
                    Li(f"Full Name: {submitted_data['full_name']}"),
                    Li(f"Title: {submitted_data['title']}"),
                    Li(f"Department: {submitted_data['dept']}"),
                    Li(f"Research Type: {submitted_data['research_type']}"),
                    Li(f"Email: {submitted_data['email']}"),
                    Li(f"Description: {submitted_data['description']}"),
                    Li(f"Post Forum: {'Yes' if submitted_data['post_forum'] else 'No'}"),
                    Li(f"Created At: {submitted_data['created_at']}")
                    ]),
    
                A(href="/")("Submit another form")
            )
        else:
            #print("Error inserting data:", response.error_message)
            return Titled("Error", 
                P("An error occurred while submitting the form. Please try again later."),
                P(f"Error Details: {response.error_message}")
            )

# Run the server
serve()