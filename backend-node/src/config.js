const path = require("path");
const fs = require("fs");

// 从项目根目录的 config.json 读取配置
const configPath = path.resolve(__dirname, "..", "..", "config.json");
const cfg = JSON.parse(fs.readFileSync(configPath, "utf-8"));

// JSON 数据文件路径，支持绝对/相对路径
const dataFile = cfg.node_data_file || "./data/chat_memory.json";
const absoluteDataFile = path.isAbsolute(dataFile)
  ? dataFile
  : path.resolve(__dirname, "..", dataFile);

// 确保数据目录存在
const dataDir = path.dirname(absoluteDataFile);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// 解析模型列表
const models = Array.isArray(cfg.models) && cfg.models.length ? cfg.models : [];
const defaultModelObj = models.find((m) => m.default) || models[0] || {};
const defaultModel = defaultModelObj.name || "glm-4.7-flash";
const availableModels = models.map((m) => m.name).filter(Boolean);

/**
 * 按模型名查找对应的 api_key 和 base_url。
 * 找不到时回退到默认模型配置。
 * @param {string} name
 * @returns {{ apiKey: string, baseUrl: string }}
 */
function getModelConfig(name) {
  const found = models.find((m) => m.name === name) || defaultModelObj;
  return {
    apiKey: found.api_key || "",
    baseUrl: found.base_url || "https://api.openai.com/v1",
  };
}

module.exports = {
  port: cfg.node_port || 8001,
  corsOrigins: Array.isArray(cfg.cors_origins)
    ? cfg.cors_origins
    : ["http://localhost:5173", "http://127.0.0.1:5173"],
  openaiModel: defaultModel,
  availableModels,
  historyLimit: cfg.history_limit || 30,
  dataFile: absoluteDataFile,
  getModelConfig,
};
