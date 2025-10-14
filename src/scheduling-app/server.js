const express = require("express");
const mongoose = require("mongoose");
const bodyParser = require("body-parser");
const path = require("path");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, "public")));

// View engine
app.set("view engine", "ejs");

// Routes
app.get("/", (req, res) => {
  res.render("index");
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
