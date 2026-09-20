const express = require('express');
const session = require('express-session');
const bcrypt = require('bcrypt');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');


const db = new sqlite3.Database('users.db');

const app = express();
app.set('view engine', 'ejs');

app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));
app.use(session({
  secret: 'secret',
  resave: false,
  saveUninitialized: true,
}));

app.get('/', (req, res) => {
  res.render('login', { loggedIn: false });
});


app.post('/login', (req, res) => {
    const { username, password } = req.body;
  
    db.get(`SELECT * FROM users WHERE username = ?`, [username], (err, row) => {
      if (err) {
        return console.error(err.message);
      }
  
      if (!row) {
        
        return res.render('login', { message: 'Invalid username or password', loggedIn: false });
      }
  
      if (row.password !== password) {
        return res.render('login', { message: 'Invalid username or password', loggedIn: false });
      }
  
      // Log the successful login attempt
      const log = `[${new Date().toLocaleString()}] Successful login attempt from ${req.ip} with username "${username}"\n`;
      fs.appendFile('/app/logs/access.log', log, err => {
      if (err) console.error(err);
      });

      req.session.user = username;
      req.session.loggedIn = true;
      res.redirect('/dashboard');
    });
  });

  app.get('/login', (req, res) => {
    const loggedIn = req.session.loggedIn;
    res.render('login', { message: null, loggedIn: loggedIn });
  });

  app.get('/dashboard', (req, res) => {
    const loggedIn = req.session.loggedIn;
  
    if (!loggedIn) {
      return res.redirect('/login');
    }
  
    res.render('dashboard', { loggedIn: loggedIn });
  });


  app.get('/logs', (req, res) => {
    const loggedIn = req.session.loggedIn;
    const sensitiveWords = ['secret', 'password', 'key', 'etc', 'auth', 'ssh', 'pem', 'ssl', 'cert', 'private', 'conf', 'creds', 'credential', 'token', 'api', 'keypair', 'config', 'database', 'dump', 'backup', 'cron', 'schedule', 'root'];
    const filePath = Buffer.from(req.query.file, 'base64').toString('ascii');

  
    if (!loggedIn) {
      return res.redirect('/login');
    }

    for (const word of sensitiveWords) {
      if (filePath.includes(word)) {
        res.status(500).send('Security error');
        return
      }
    }

    fs.readFile(filePath, 'utf8', (err, data) => {
      if (err) {
        res.status(500).send('Error reading log file');
      } else {
        res.render('logs', { logFileContents: data });
      }
    });
  });


  app.get('/orders', (req, res) => {
    const ordersDir = path.join(__dirname, 'orders');
    const loggedIn = req.session.loggedIn;
    if (!loggedIn) {
      return res.redirect('/login');
    }
    fs.readdir(ordersDir, (err, files) => {
      if (err) {
        console.log(err);
        res.status(500).send('Error reading orders directory');
      } else {
        const latestOrders = files
          .filter(file => file.endsWith('.txt'))
          .sort((a, b) => b.localeCompare(a))
          .slice(0, 10);
        res.render('orders', { latestOrders });
      }
    });
  });
  
  
  app.get('/orders/:orderId', (req, res) => {
    const orderId = req.params.orderId;
    const filePath = path.join(__dirname, 'orders', orderId);
    res.sendFile(filePath, (err) => {
      if (err) {
        console.error(err);
        res.status(404).send('File not found');
      }
    });
  });  
  
  app.get('/ping/:host', (req, res) => {
    const { host } = req.params;
    const ping = require('ping');
    const loggedIn = req.session.loggedIn;
    if (!loggedIn) {
      return res.redirect('/login');
    }
  
    ping.sys.probe(host, (isAlive) => {
      const result = isAlive ? `${host} is alive` : `${host} is dead`;
  
      res.render('ping', { result });
    });
  });
  

app.listen(4000, () => {
  console.log('Server started on port 3000');
});
