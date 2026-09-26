const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const request = require('request');
const cheerio = require('cheerio');

app.use(bodyParser.urlencoded({ extended: true }));

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
      <style>
		body {
			color: #800000;
			font-family: "Comic Sans MS", cursive, sans-serif;
			text-align: center;
			background-color: #F0E68C;
		}
		
		h1 {
			font-size: 40px;
			margin-bottom: 0;
		}
		
		#form-container {
			background-color: #FFA07A;
			border: 5px solid #CD5C5C;
			border-radius: 25px;
			display: inline-block;
			margin-top: 20px;
			padding: 10px;
			text-align: left;
			width: 500px;
		}
		
		label {
			display: block;
			font-size: 24px;
			margin-top: 10px;
		}
		
		input[type="text"] {
			border: none;
			font-size: 24px;
			margin-top: 10px;
			padding: 5px;
			width: 80%;
		}
		
		button[type="submit"] {
			background-color: #CD5C5C;
			border: none;
			color: #FFFFFF;
			font-size: 24px;
			margin-top: 10px;
			padding: 10px;
			width: 100%;
		}
		
		.result {
			background-color: #FFFFFF;
			border: 5px solid #CD5C5C;
			border-radius: 25px;
			display: inline-block;
			margin-top: 20px;
			padding: 10px;
			text-align: left;
			width: 500px;
		}
		
		.result-title {
			font-size: 32px;
			margin-bottom: 0;
			margin-top: 10px;
		}
		
		.result-url {
			color: #800000;
			font-size: 18px;
			font-style: italic;
			margin-bottom: 10px;
			margin-top: 0;

		}
	</style>
      </head>
      <body>
        <form method="POST" action="/title">
          <label for="url">Enter a URL:</label>
          <input type="text" name="url" id="url">
		  <input type="hidden" name="element" value="title">
          <button type="submit">Get title</button>
        </form>
		<img src="https://web.archive.org/web/20090829024314im_/http://geocities.com/okitsugu/underconstruction.gif" style="horizontal-align:middle">
      </body>

	  <!-- flag3GoesHere -->
    </html>
  `);
});

app.post('/title', (req, res) => {
  const url = req.body.url;
  const htmlsection = req.body.element;
  if (url == "169.254.169.254" || url == "http://169.254.169.254") {
    res.send('We told you no escapes! flag2GoesHere');
	return;
  }
  if (url == "http://localhost:3000/admin") {
    res.send('Welcome Admin! flag5GoesHere \n Sm9rZXI6WXJPeW5hcFNiZXJpcmUxMjMKQWtlY2hpOkNuYXBueHJmTmVyWXZzciEhCk1vcmdhbmE6TmFhVmZPbnI8Mw==');
	return;
  }
  request(url, (error, response, body) => {
    if (error) {
      res.send('Error retrieving URL');
    } else {
      const $ = cheerio.load(body);
      const title = $(htmlsection).text();
      res.send(`Title of ${url} is: ${title}`);
    }
  });
});

app.get('/admin', (req, res) => {
    res.send('Security Error: Only accessible via internal addresses');
  });

app.listen(3000,'0.0.0.0', () => console.log('App listening on port 3000'));




const app2 = express();



app2.use(bodyParser.urlencoded({ extended: true }));

app2.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
      <style>
		body {
			background-color: #F0E68C;
			color: #800000;
			font-family: "Comic Sans MS", cursive, sans-serif;
			text-align: center;
		}
		
		h1 {
			font-size: 40px;
			margin-bottom: 0;
		}
		
		#form-container {
			background-color: #FFA07A;
			border: 5px solid #CD5C5C;
			border-radius: 25px;
			display: inline-block;
			margin-top: 20px;
			padding: 10px;
			text-align: left;
			width: 500px;
		}
		
		label {
			display: block;
			font-size: 24px;
			margin-top: 10px;
		}
		
		input[type="text"] {
			border: none;
			font-size: 24px;
			margin-top: 10px;
			padding: 5px;
			width: 80%;
		}
		
		button[type="submit"] {
			background-color: #CD5C5C;
			border: none;
			color: #FFFFFF;
			font-size: 24px;
			margin-top: 10px;
			padding: 10px;
			width: 100%;
		}
		
		.result {
			background-color: #FFFFFF;
			border: 5px solid #CD5C5C;
			border-radius: 25px;
			display: inline-block;
			margin-top: 20px;
			padding: 10px;
			text-align: left;
			width: 500px;
		}
		
		.result-title {
			font-size: 32px;
			margin-bottom: 0;
			margin-top: 10px;
		}
		
		.result-url {
			color: #800000;
			font-size: 18px;
			font-style: italic;
			margin-bottom: 10px;
			margin-top: 0;
		}
	</style>
      </head>
      <title>
        <h1>flagGoesHere</h1>
      </title>
    </html>
  `);
});

app2.get('/keys', (req, res) => {
	res.send(`
	<html>
      <title>Secret Keys</title>
	  <body>I wanted to put an SSH key here, but Docker is hard. flag6GoesHere</body>
	</html>
	`);
});


app2.listen(3030,'0.0.0.0', () => console.log('App listening on port 3030'));