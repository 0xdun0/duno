const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bcrypt = require('bcrypt');

const app = express();
const dbPath = path.resolve(__dirname, 'users.db');
const db = new sqlite3.Database(dbPath);

// Set up the view engine
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

// Set up the middleware to parse request bodies
app.use(express.urlencoded({ extended: true }));

// Set up a route for the login page
app.get('/', (req, res) => {
  res.render('login');
});

// Set up a route to handle login form submissions
app.post('/', (req, res) => {
  const username = req.body.username;
  const password = req.body.password;

  // Check if the username and password are correct
  db.get('SELECT password FROM users WHERE username = ?', [username], (err, row) => {
    if (err) {
      console.error(err.message);
      return res.status(500).send('Internal server error');
    }
    if (!row) {
      return res.status(401).render('login', { error: 'Invalid username or password' });
    }
    bcrypt.compare(password, row.password, (err, result) => {
      if (err) {
        console.error(err.message);
        return res.status(500).send('Internal server error');
      }
      if (!result) {
        return res.status(401).render('login', { error: 'Invalid username or password' });
      }
      res.send('You have successfully logged in!');
    });
  });
});

// Start the server
const port = 3000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
