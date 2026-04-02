const path = require("path");
const fs = require("fs");
require("dotenv").config();

const dataFile = process.env.DATA_FILE || "./data/chat_memory.json";
const absoluteDataFile = path.isAbsolute(dataFile)
  ? dataFile
  : path.resolve(__dirname, "..", dataFile);

const dataDir = path.dirname(absoluteDataFile);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

module.exports = {
  port: Number(process.env.PORT || 8001),
  corsOrigins: (process.env.CORS_ORIGINS || "http://localhost:5173,http://127.0.0.1:5173")
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean),
  openaiApiKey: process.env.OPENAI_API_KEY || "",
  openaiBaseUrl: process.env.OPENAI_BASE_URL || "https://open.bigmodel.cn/api/paas/v4",
  openaiModel: process.env.OPENAI_MODEL || "glm-4.7-flash",
  historyLimit: Number(process.env.HISTORY_LIMIT || 30),
  dataFile: absoluteDataFile,
};
