const dotenv = require('dotenv')
const path = require('path')

dotenv.config({
  path: path.resolve(__dirname, '../.env')
});

module.exports = {
  typescript: {
    ignoreBuildErrors: true
  },
  env: {
    NEXT_APP_WS_URL: process.env.NEXT_APP_WS_URL,
    NEXT_APP_API_URL: process.env.NEXT_APP_API_URL,
    NEXT_APP_CHART_API_URL: process.env.NEXT_APP_CHART_API_URL,
    NEXT_APP_OPTS_API_URL: process.env.NEXT_APP_OPTS_API_URL,
    NEXT_APP_EVENT_API_URL: process.env.NEXT_APP_EVENT_API_URL,
    CHART_TIME_INTERVAL: process.env.CHART_TIME_INTERVAL
  }
}