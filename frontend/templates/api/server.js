const express = require("express");
const cors = require("cors");
const path = require("path");
const checkAccessTokenRoutes = require("./check-access-token");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname, "..")));

// API Routes
app.use("/api", checkAccessTokenRoutes);

// Serve index.html for all routes
app.get("*", (req, res) => {
    res.sendFile(path.join(__dirname, "..", "index.html"));
});

app.listen(PORT, () => {
    console.log(`Server đang chạy trên cổng ${PORT}`);
});
