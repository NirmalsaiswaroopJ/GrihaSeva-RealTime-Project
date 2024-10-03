# GrihaSeva - Your One-Stop Solution for Home Services

Welcome to **GrihaSeva**! This platform offers a wide array of professional home services such as cleaning, plumbing, electrical repairs, and women-exclusive services like beauty treatments. Our aim is to make booking these services as easy as possible through a user-friendly interface.

## Project Overview

GrihaSeva is designed to provide users with quick and reliable home services. Users can browse through service categories, book services, and register either as a customer or as a service provider. We also offer interactive features like a chatbot to assist users in making decisions and bookings.

### Key Features

- **Service Categories:** From electrical to beauty treatments, with a dedicated section for women-exclusive services.
- **Booking & Registration Forms:** Users can easily book services or register as customers/service providers.
- **Interactive Chatbot:** Provides assistance with service information and helps guide users through the booking process.
- **Responsive Design:** Tailored for a seamless experience on mobile, tablet, and desktop devices.

## Demo

You can view the static version of the GrihaSeva project here - [Website](https://grihasevaservice.netlify.app/).

## Video Walkthrough

I’m excited to share a video walkthrough of *GrihaSeva*, my dynamic home services platform! This video highlights the real-time features, such as service booking, provider dashboards, and the chatbot feature and explains one of the real-time functionalities - *Service Booking*

[![Watch the video](https://img.youtube.com/vi/mxShNzMWvJA/hqdefault.jpg)](https://www.youtube.com/watch?v=mxShNzMWvJA)

## Medium Article

I’ve written a detailed Medium article explaining the development process of *GrihaSeva*, including the dynamic real-time features such as service booking, provider dashboards, password reset with Flask-Mail, and more.

[Read the Full Article on Medium](https://medium.com/@nirmalsai22/building-grihaseva-a-dynamic-home-services-web-app-with-real-time-features-77690937741f)

### Highlights from the Article:
- Real-time service booking and provider management.
- Secure password reset using Flask-Mail.
- Integration of MySQL database for managing users and services.
- Role-based access control for users and service providers.

Check out the full article to learn more about the technical architecture and dynamic features of the *GrihaSeva* platform.

## Project Structure

Here is an overview of the project structure with links to key files and directories:

- [**static/**](./static)  
  Contains static assets such as images used throughout the website.
  - [**images/**](./static/images)  
    This folder holds images for various services, such as electrical, cleaning, and beauty services.
  - [**css/**](./static/css)  
    This folder holds cascading style sheets for various login and registration form webpages.
  - [**js/**](./static/js)  
    This folder holds javascript for various login webpages.
    
- [**templates/**](./templates)  
  Contains the HTML templates for different pages of the web application.
  - [**index.html**](./templates/index.html)  
    The main landing page, which highlights service categories and the chatbot interaction.
  
- [**main.py**](./main.py)  
  The main Python script responsible for handling service requests, user sessions, and routing logic.

- [**Python Flask Code Documentation.pdf**](./Python%20Flask%20Code%20Documentation.pdf)  
  Documentation covering the routing and Flask backend implementation.

- [**GrihaSeva Project Database Queries.pdf**](./GrihaSeva%20Project%20Database%20Queries.pdf)  
  A PDF containing the SQL queries used to set up and manage the database for users, services, and providers.

- [**Libraries & Modules.pdf**](./Libraries%20&%20Modules.pdf)  
  A PDF containing detailed description and purpose of libraries and modules used in the course of project.

- [**Real Time Functionalities.pdf**](./Real%20Time%20Functionalities.pdf)  
  A detailed PDF explaining the real-time functionalities of GrihaSeva, including dynamic service booking, provider dashboards, chatbot assistance, interactive blogs with 
  emoji reactions, and secure password recovery using Flask-Mail.
  
- [**requirements.txt**](./requirements.txt)  
  A list of the Python dependencies needed to run the project locally.

- [**LICENSE**](./LICENSE)  
  The license under which this project is released.

- [**README.md**](./README.md)  
  The current project documentation.

## Forms & Routing

The GrihaSeva project implements several forms for users and service providers. These forms handle tasks such as registration and login. Each form is connected to a Python-Flask backend for server-side validation and processing. Below are some of the main forms and their routing paths:

#### 1. **User Registration Form**
  - **Route**: `/user-register`
  - **Method**: `POST`
  - **Functionality**: Allows new users to create an account by submitting personal details such as:
    - Full Name
    - Email Address
    - Password
    - Phone Number
  - **Backend Process**:
    - Validates user input (e.g., email format, password length).
    - Checks if the email already exists in the database.
    - Stores the user's data directly into the database without hashing (ensure password security is handled properly in future updates).
    - Redirects users to the login page upon successful registration.
  - **Security Considerations**:
    - Though passwords are stored as plain text for now (NOT recommended for production environments), future iterations should implement password hashing for better security.
    - Input fields are validated to prevent SQL injection or XSS attacks.
    - Email confirmation can be added to further validate users.

#### 2. **User Login Form**
  - **Route**: `/user-login`
  - **Method**: `POST`
  - **Functionality**: Allows registered users to log in by providing:
    - Email Address
    - Password
  - **Backend Process**:
    - Validates the email and password.
    - Matches the entered email and password against the stored values in the database.
    - Creates a user session upon successful authentication.
    - Redirects the user to the service dashboard after successful login.
    - Provides an error message if the credentials are incorrect.
  - **Security Considerations**:
    - Since passwords are stored in plain text, this should be considered for improvement by adding password hashing in future updates.
    - Uses sessions to maintain user authentication.
    - Implements brute-force protection by limiting the number of login attempts.

#### 3. **Provider Login Form**
  - **Route**: `/provider-login`
  - **Method**: `POST`
  - **Functionality**: Allows service providers to log in and manage their service offerings by submitting:
    - Provider ID
    - Password
  - **Backend Process**:
    - Authenticates service providers based on their unique ID and password.
    - Grants access to a dashboard where they can manage service requests, view user feedback, and update availability.
  - **Security Considerations**:
    - Provider credentials are checked against plain text data (consider adding password encryption in future versions).
    - Sessions are used to authenticate providers during their logged-in period.

## Installation

To run this project locally, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/GrihaSeva.git
    ```

2. Navigate to the project directory:
    ```bash
    cd GrihaSeva
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the Python backend:
    ```bash
    python main.py
    ```

5. Open your browser and go to `http://localhost:5000` to view the application.

## Technologies Used

- **Frontend**: HTML5, Bootstrap, JavaScript, Tailwind CSS for responsive and modern design.
- **Backend**: Python-Flask for routing and form handling.
- **Database**: Managed using SQL queries stored in `GrihaSeva Project Database Queries.pdf`.
- **Deployment**: The project is hosted using Netlify for static files.

## Code Documentation

- Detailed code documentation will be uploaded soon to explain the architecture, core modules, and custom functions used in this project.
- The upcoming documentation will include:
  - **API Endpoints and Forms**: Explanation of how data flows through routes.
  - **Error Handling and Validation**: Details about user input validation and error responses.
  - **Custom Features**: Explanation of the interactive chatbot and animations.

### Documentation Validation

To ensure the quality, accuracy, and reliability of our documentation, we have implemented the following validation methods:

- **Peer Review**:  
  The documentation has been reviewed by multiple team members and developers who provided feedback on its clarity, completeness, and adherence to best practices. All suggestions and corrections have been incorporated into the final version.

- **User Testing**:  
  We conducted testing with users unfamiliar with the project. These users followed the documentation step-by-step to set up, install, and navigate the system. Feedback from this testing process was used to improve clarity and ensure that the instructions are easy to follow.

- **Functional Testing**:  
  Every step in the documentation has been executed exactly as described. This includes:
  - Setting up the environment.
  - Installing required dependencies.
  - Running the project locally.
  - Testing the forms and routing to ensure they function as expected.
  
  This ensures that the provided instructions lead to a successful setup and that the project behaves as intended when following the documentation.

By following these validation processes, we strive to provide a reliable, clear, and user-friendly guide for anyone interacting with the GrihaSeva project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For further information or queries, please reach out via email at [nirmalsai22@gmail.com].

Feel free to connect with me on Linkedin - [LinkedIn](https://www.linkedin.com/in/nirmal-sai-swaroop-janapaneedi-4aa5632a7/)
