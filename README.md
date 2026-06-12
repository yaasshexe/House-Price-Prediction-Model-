##  Project Structure

##  Tech Stack
| **Frontend** HTML5, CSS3 , Vanilla JS 
| **Backend** Python, Flask, Flask-CORS
| **ML Model** scikit-learn `GradientBoostingRegressor` 
| **Data** Synthetic Pune housing data (3000 samples) 
| **Serialisation**`pickle` 

##  How to Run in VS Code — Step by Step

###  Prerequisites
- **Python 3.9+** installed and added to PATH
- **VS Code** installed
- **Git** (optional, for version control)

### Step 1️ — Open the Project in VS Code

1. Open VS Code
2. File → Open Folder
3. Navigate to the project directory and click "Select Folder"

### Step 2️ — Open the Integrated Terminal

Press: **`Ctrl + `` `` (backtick)**

Or: `Terminal → New Terminal`

You should see the terminal panel open at the bottom of VS Code.

### Step 3️ — Create & Activate Virtual Environment

**Windows:**

python -m venv venv
venv\Scripts\activate

### Step 4️ — Install Dependencies


pip install -r requirements.txt

### Step 5️ — Train the ML Model *(first time only)*

python model/price_model.py

### Step 6️ — Start the Flask Server

python server/app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Root     : C:\path\to\project
   Client   : C:\path\to\project\client
   API base : http://127.0.0.1:5000/api
   App URL  : http://127.0.0.1:5000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 * Running on http://127.0.0.1:5000
 * Debug mode: on

**Server is running!** 

### Step 7️ — Open in Browser

Click or visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Step 8️ — Test the Application

1. **Fill in the form** with property details:
   - Select a location (e.g., Baner)
   - Enter area (e.g., 1200 sq ft)
   - Select BHK type (1BHK, 2BHK, 3BHK, 4BHK)
   - Choose amenities (Gym, Pool, Security, etc.)
   
###  To Stop the Server

Press: **`Ctrl + C`** in the terminal running the Flask server

## 📄 License

MIT License — Free to use for academic and personal projects.

