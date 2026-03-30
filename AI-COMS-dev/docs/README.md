### **How to Start a React Frontend Project?**
If you want to use **React, Bootstrap, SASS, HTML, and CSS**, follow these steps:

---

## **1️⃣ Initializing a React Project**
To create a new frontend project, run the following commands in the terminal:
```sh
cd frontend
npx create-react-app my-app
cd my-app
npm install
```
Or, using **Vite** for a faster setup:
```sh
cd frontend
npm create vite@latest my-app --template react
cd my-app
npm install
```
Start the development server:
```sh
npm start
```
📌 **Local Server:** `http://localhost:3000`

---

## **2️⃣ Project Structure**
```
/frontend
 ├── /my-app
 │   ├── /public        # Static assets (images, icons)
 │   ├── /src
 │   │   ├── /components  # Reusable UI components
 │   │   │   ├── /Navbar   # Navbar component
 │   │   │   │   ├── Navbar.js
 │   │   │   │   ├── Navbar.scss
 │   │   │   ├── /Footer   # Footer component
 │   │   │   │   ├── Footer.js
 │   │   │   │   ├── Footer.scss
 │   │   │   ├── /Button   # Reusable button component
 │   │   │   │   ├── Button.js
 │   │   │   │   ├── Button.scss
 │   │   ├── /pages       # Page components
 │   │   ├── /assets      # Styles and resources
 │   │   │   ├── /scss       # SASS files
 │   │   │   │   ├── /components         # Components styles
 │   │   │   │   │   ├──Navbar         # Navbar  
 │   │   │   │   ├── _variables.scss  # Bootstrap overrides
 │   │   │   │   ├── _global.scss     # Global styles
 │   │   │   │   ├──  styles.scss     # Main SASS file (imports all partials)
 │   │   ├── /services    # API requests
 │   │   ├── App.js       # Main App component
 │   │   ├── index.js     # Root file
 │   ├── package.json     # React dependencies
 │   ├── .gitignore       # Ignore file for Git
```

---

## **3️⃣ Installing Dependencies**
### **1. Install Bootstrap & SASS**
```sh
npm install bootstrap sass
```
Then, import Bootstrap in `index.js`:
```javascript
import 'bootstrap/dist/css/bootstrap.min.css';
```
### **2. SASS Setup**
Create `src/assets/scss/styles.scss` and add:
```scss
@import "variables";
@import "global";
```
Customize Bootstrap in `src/assets/scss/_variables.scss`:
```scss
$primary: #007bff;
$secondary: #6c757d;
$danger: #dc3545;
@import "bootstrap/scss/bootstrap";
```
Import the main SCSS file in `App.js`:
```javascript
import "./assets/scss/styles.scss";
```

---

## **4️⃣ Adding Pages & Navbar**
Create reusable components inside `src/components/` and pages inside `src/pages/`.

✅ **Example: `Navbar.js` (`src/components/Navbar.js`)**
```javascript
import React from "react";
import { Link } from "react-router-dom";

const Navbar = () => {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container">
        <Link className="navbar-brand" to="/">My Website</Link>
        <div className="collapse navbar-collapse">
          <ul className="navbar-nav ms-auto">
            <li className="nav-item"><Link className="nav-link" to="/">Home</Link></li>
            <li className="nav-item"><Link className="nav-link" to="/about">About</Link></li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
```

---

## **5️⃣ Setting Up React Router**
```sh
npm install react-router-dom
```
Modify `App.js` to include routes:
```javascript
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import About from "./pages/About";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Router>
  );
}
export default App;
```

---

## **6️⃣ Connecting to Backend**
If the frontend needs to communicate with the backend, create `src/services/api.js`:
```javascript
import axios from "axios";
const API_URL = "http://localhost:8000";
export const fetchData = async () => {
  const response = await axios.get(`${API_URL}/data`);
  return response.data;
};
```

---

## **Summary**
1️⃣ **Create a React project (`npx create-react-app`).**  
2️⃣ **Organize files (`components`, `pages`, `assets/scss`).**  
3️⃣ **Install and configure Bootstrap & SASS.**  
4️⃣ **Use React Router for navigation.**  
5️⃣ **Prepare API services for backend integration.**  





