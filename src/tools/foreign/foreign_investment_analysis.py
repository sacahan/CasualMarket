"""
外資投資分析工具
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ..base import ToolBase


class ForeignInvestmentAnalysisTool(ToolBase):
    """
    外資投資分析工具。

    提供外資持股、買賣超、投資趨勢等分析服務。
    """

    def __init__(self):
        super().__init__("foreign_investment_analysis")
        self.openapi_client = OpenAPIClient()

    async def execute(
        self, analysis_type: str = "holdings", symbol: str = "", **kwargs
    ) -> dict[str, Any]:
        """
        執行外資投資分析。

        Args:
            analysis_type: 分析類型 (holdings, trading, trends, summary)
            symbol: 股票代碼 (可選，留空則分析全市場)

        Returns:
            包含外資投資分析結果的字典
        """
        try:
            self.logger.info(f"執行外資投資分析: type={analysis_type}, symbol={symbol}")

            analysis_results = {}

            if analysis_type in ["holdings", "all"]:
                # 取得外資持股排行
                foreign_holdings_data = await self.openapi_client.get_data(
                    "/fund/MI_QFIIS_sort_20"
                )
                if foreign_holdings_data:
                    analysis_results["foreign_holdings"] = (
                        self._analyze_foreign_holdings(foreign_holdings_data, symbol)
                    )

            if analysis_type in ["trading", "all"]:
                # 取得券商基本資料 (可用於分析外資券商)
                broker_data = await self.openapi_client.get_data(
                    "/brokerService/brokerList"
                )
                if broker_data:
                    analysis_results["foreign_brokers"] = self._analyze_foreign_brokers(
                        broker_data
                    )

            if analysis_type in ["trends", "all"]:
                # 分析外資投資趨勢 (基於持股變化)
                if "foreign_holdings" in analysis_results:
                    analysis_results["investment_trends"] = (
                        self._analyze_investment_trends(
                            analysis_results["foreign_holdings"]
                        )
                    )

            # 生成綜合分析
            if analysis_type == "all" or analysis_type == "summary":
                analysis_results["investment_summary"] = (
                    self._generate_investment_summary(analysis_results, symbol)
                )

            return {
                "status": "success",
                "data": {
                    "analysis_type": analysis_type,
                    "symbol": symbol,
                    "analysis_results": analysis_results,
                },
            }

        except Exception as e:
            self.logger.error(f"外資投資分析失敗: {e}")
            return self._error_response(str(e))

    def _analyze_foreign_holdings(self, holdings_data: list, symbol: str = "") -> dict:
        """分析外資持股"""
        holdings_stats = {
            "total_holdings": len(holdings_data),
            "top_holdings": [],
            "sector_distribution": {},
            "holding_concentration": {},
            "investment_focus": [],
        }

        # 過濾指定股票
        if symbol:
            holdings_data = [
                item
                for item in holdings_data
                if symbol in str(item.get("證券代號", ""))
                or symbol in str(item.get("證券名稱", ""))
            ]

        # 分析前 20 大持股
        for item in holdings_data[:20]:
            holding_info = {
                "stock_code": item.get("證券代號", ""),
                "stock_name": item.get("證券名稱", ""),
                "foreign_holding_shares": int(item.get("外陸資持股股數", 0) or 0),
                "total_issued_shares": int(item.get("已發行股數", 0) or 0),
                "holding_percentage": float(item.get("持股比率", 0) or 0),
                "previous_holding": int(item.get("前日持股", 0) or 0),
                "daily_change": int(item.get("持股異動", 0) or 0),
            }

            # 計算持股變化百分比
            if holding_info["previous_holding"] > 0:
                holding_info["change_percentage"] = (
                    holding_info["daily_change"]
                    / holding_info["previous_holding"]
                    * 100
                )
            else:
                holding_info["change_percentage"] = 0

            holdings_stats["top_holdings"].append(holding_info)

        # 分析持股集中度
        if holdings_stats["top_holdings"]:
            total_foreign_shares = sum(
                h["foreign_holding_shares"] for h in holdings_stats["top_holdings"]
            )
            top_5_shares = sum(
                h["foreign_holding_shares"] for h in holdings_stats["top_holdings"][:5]
            )
            top_10_shares = sum(
                h["foreign_holding_shares"] for h in holdings_stats["top_holdings"][:10]
            )

            holdings_stats["holding_concentration"] = {
                "total_foreign_shares": total_foreign_shares,
                "top_5_concentration": (
                    top_5_shares / total_foreign_shares * 100
                    if total_foreign_shares > 0
                    else 0
                ),
                "top_10_concentration": (
                    top_10_shares / total_foreign_shares * 100
                    if total_foreign_shares > 0
                    else 0
                ),
                "concentration_level": (
                    "高度集中"
                    if top_5_shares / total_foreign_shares > 0.4
                    else "分散投資"
                ),
            }

        # 分析投資焦點 (持股比例最高的股票)
        high_percentage_holdings = [
            h for h in holdings_stats["top_holdings"] if h["holding_percentage"] > 10
        ]
        holdings_stats["investment_focus"] = sorted(
            high_percentage_holdings,
            key=lambda x: x["holding_percentage"],
            reverse=True,
        )[:10]

        # 行業分佈分析 (簡化版，基於股票名稱關鍵字)
        sector_counts = self._categorize_by_sector(holdings_stats["top_holdings"])
        holdings_stats["sector_distribution"] = sector_counts

        return holdings_stats

    def _analyze_foreign_brokers(self, broker_data: list) -> dict:
        """分析外資券商"""
        foreign_broker_stats = {
            "total_brokers": len(broker_data),
            "foreign_brokers": [],
            "domestic_brokers": [],
            "broker_distribution": {},
        }

        # 識別外資券商 (基於名稱關鍵字)
        foreign_keywords = [
            "摩根",
            "高盛",
            "美林",
            "瑞銀",
            "花旗",
            "德意志",
            "野村",
            "麥格理",
            "星展",
        ]

        for broker in broker_data:
            broker_info = {
                "broker_code": broker.get("證券商代號", ""),
                "broker_name": broker.get("證券商名稱", ""),
                "address": broker.get("地址", ""),
                "phone": broker.get("電話", ""),
            }

            # 判斷是否為外資券商
            is_foreign = any(
                keyword in broker_info["broker_name"] for keyword in foreign_keywords
            )

            if is_foreign:
                foreign_broker_stats["foreign_brokers"].append(broker_info)
            else:
                foreign_broker_stats["domestic_brokers"].append(broker_info)

        # 券商分佈統計
        foreign_broker_stats["broker_distribution"] = {
            "foreign_count": len(foreign_broker_stats["foreign_brokers"]),
            "domestic_count": len(foreign_broker_stats["domestic_brokers"]),
            "foreign_ratio": len(foreign_broker_stats["foreign_brokers"])
            / len(broker_data)
            * 100,
        }

        return foreign_broker_stats

    def _analyze_investment_trends(self, holdings_data: dict) -> dict:
        """分析外資投資趨勢"""
        trend_stats = {
            "buying_trend": [],
            "selling_trend": [],
            "holding_changes": {},
            "sector_preferences": {},
            "investment_strategy": "",
        }

        top_holdings = holdings_data.get("top_holdings", [])

        # 分析買賣趨勢
        buying_stocks = [h for h in top_holdings if h["daily_change"] > 0]
        selling_stocks = [h for h in top_holdings if h["daily_change"] < 0]

        # 按變化量排序
        trend_stats["buying_trend"] = sorted(
            buying_stocks, key=lambda x: x["daily_change"], reverse=True
        )[:10]

        trend_stats["selling_trend"] = sorted(
            selling_stocks, key=lambda x: abs(x["daily_change"]), reverse=True
        )[:10]

        # 持股變化統計
        total_buying = sum(h["daily_change"] for h in buying_stocks)
        total_selling = sum(abs(h["daily_change"]) for h in selling_stocks)
        net_flow = total_buying - total_selling

        trend_stats["holding_changes"] = {
            "total_buying": total_buying,
            "total_selling": total_selling,
            "net_flow": net_flow,
            "buying_stocks_count": len(buying_stocks),
            "selling_stocks_count": len(selling_stocks),
            "market_sentiment": (
                "看多" if net_flow > 0 else "看空" if net_flow < 0 else "中性"
            ),
        }

        # 分析投資策略
        high_percentage_changes = [
            h for h in top_holdings if abs(h.get("change_percentage", 0)) > 5
        ]
        if len(high_percentage_changes) > len(top_holdings) * 0.3:
            trend_stats["investment_strategy"] = "積極調整投資組合"
        elif net_flow > 0:
            trend_stats["investment_strategy"] = "增持看好標的"
        elif net_flow < 0:
            trend_stats["investment_strategy"] = "減持獲利了結"
        else:
            trend_stats["investment_strategy"] = "維持現有部位"

        return trend_stats

    def _generate_investment_summary(self, analysis_results: dict, symbol: str) -> dict:
        """生成外資投資摘要"""
        summary = {
            "market_impact": "",
            "investment_insights": [],
            "risk_assessment": "",
            "strategic_recommendations": [],
        }

        # 市場影響評估
        if "foreign_holdings" in analysis_results:
            holdings_data = analysis_results["foreign_holdings"]
            concentration = holdings_data.get("holding_concentration", {})

            if concentration.get("concentration_level") == "高度集中":
                summary["market_impact"] = "外資持股高度集中，對特定股票影響顯著"
            else:
                summary["market_impact"] = "外資持股相對分散，市場影響較為溫和"

        # 投資洞察
        if "investment_trends" in analysis_results:
            trends_data = analysis_results["investment_trends"]
            holding_changes = trends_data.get("holding_changes", {})

            market_sentiment = holding_changes.get("market_sentiment", "中性")
            net_flow = holding_changes.get("net_flow", 0)

            summary["investment_insights"] = [
                f"外資整體市場情緒: {market_sentiment}",
                f"淨流入/流出: {net_flow:,} 股",
                f"買超股票數: {holding_changes.get('buying_stocks_count', 0)}",
                f"賣超股票數: {holding_changes.get('selling_stocks_count', 0)}",
            ]

            # 風險評估
            if abs(net_flow) > 1000000:  # 超過 100 萬股的變化
                summary["risk_assessment"] = "外資大幅調整部位，市場波動風險較高"
            elif market_sentiment == "看空":
                summary["risk_assessment"] = "外資偏向賣超，短期可能面臨壓力"
            else:
                summary["risk_assessment"] = "外資投資行為相對穩定，市場風險可控"

        # 策略建議
        if symbol:
            summary["strategic_recommendations"] = [
                f"建議關注 {symbol} 的外資持股變化",
                "注意外資買賣超對股價的短期影響",
                "可參考外資投資策略調整投資組合",
            ]
        else:
            summary["strategic_recommendations"] = [
                "跟隨外資買超股票可能獲得資金推升效應",
                "避開外資大幅賣超的股票以降低風險",
                "關注外資投資的行業偏好調整配置",
            ]

        return summary

    def _categorize_by_sector(self, holdings: list) -> dict:
        """根據股票名稱簡單分類行業"""
        sector_mapping = {
            "科技": ["台積電", "聯發科", "廣達", "鴻海", "緯創", "仁寶", "英業達"],
            "金融": ["台積電", "中信金", "富邦金", "國泰金", "第一金", "兆豐金"],
            "傳產": ["台塑", "南亞", "台化", "台泥", "亞泥", "中鋼"],
            "生技": ["台康生技", "基亞", "浩鼎", "中天"],
            "電信": ["中華電", "台灣大", "遠傳"],
            "其他": [],
        }

        sector_counts = {sector: 0 for sector in sector_mapping.keys()}

        for holding in holdings:
            stock_name = holding.get("stock_name", "")
            categorized = False

            for sector, keywords in sector_mapping.items():
                if sector == "其他":
                    continue

                if any(keyword in stock_name for keyword in keywords):
                    sector_counts[sector] += 1
                    categorized = True
                    break

            if not categorized:
                sector_counts["其他"] += 1

        return sector_counts
