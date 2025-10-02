"""
ETF 分析工具
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ..base import ToolBase


class ETFAnalysisTool(ToolBase):
    """
    ETF (Exchange Traded Fund) 分析工具。

    提供 ETF 排名、績效分析、投資組合分析等服務。
    """

    def __init__(self):
        super().__init__("etf_analysis")
        self.openapi_client = OpenAPIClient()

    async def execute(
        self, analysis_type: str = "ranking", category: str = "all", **kwargs
    ) -> dict[str, Any]:
        """
        執行 ETF 分析。

        Args:
            analysis_type: 分析類型 (ranking, performance, composition)
            category: ETF 類別 (all, domestic, international, sector)

        Returns:
            包含 ETF 分析結果的字典
        """
        try:
            self.logger.info(
                f"執行 ETF 分析: type={analysis_type}, category={category}"
            )

            analysis_results = {}

            if analysis_type in ["ranking", "all"]:
                # 取得 ETF 排名資料
                etf_ranking_data = await self.openapi_client.get_data(
                    "/ETFReport/ETFRank"
                )
                if etf_ranking_data:
                    analysis_results["etf_ranking"] = self._analyze_etf_ranking(
                        etf_ranking_data, category
                    )

            if analysis_type in ["performance", "all"]:
                # 取得每日交易資料進行績效分析
                trading_data = await self.openapi_client.get_data(
                    "/exchangeReport/STOCK_DAY_ALL"
                )
                if trading_data:
                    etf_trading_data = self._filter_etf_trading_data(trading_data)
                    analysis_results["performance_analysis"] = (
                        self._analyze_etf_performance(etf_trading_data)
                    )

            if analysis_type in ["composition", "all"]:
                # 分析 ETF 組成和分佈
                if "etf_ranking" in analysis_results:
                    analysis_results["composition_analysis"] = (
                        self._analyze_etf_composition(analysis_results["etf_ranking"])
                    )

            # 生成投資建議
            if analysis_type == "all":
                analysis_results["investment_recommendations"] = (
                    self._generate_etf_recommendations(analysis_results)
                )

            return {
                "status": "success",
                "data": {
                    "analysis_type": analysis_type,
                    "category": category,
                    "analysis_results": analysis_results,
                },
            }

        except Exception as e:
            self.logger.error(f"ETF 分析失敗: {e}")
            return self._error_response(str(e))

    def _analyze_etf_ranking(self, etf_data: list, category: str) -> dict:
        """分析 ETF 排名"""
        ranking_stats = {
            "total_etfs": len(etf_data),
            "top_performers": [],
            "most_active": [],
            "category_breakdown": {},
            "performance_metrics": {},
        }

        # 過濾和排序 ETF
        filtered_etfs = []
        for item in etf_data:
            etf_info = {
                "etf_code": item.get("證券代號", ""),
                "etf_name": item.get("證券名稱", ""),
                "trading_accounts": int(item.get("成交帳戶數", 0) or 0),
                "trading_volume": float(item.get("成交股數", 0) or 0),
                "trading_value": float(item.get("成交金額", 0) or 0),
                "average_transaction": float(item.get("平均每戶成交金額", 0) or 0),
            }

            # 根據類別過濾
            if category != "all":
                if category == "domestic" and not self._is_domestic_etf(
                    etf_info["etf_name"]
                ):
                    continue
                elif category == "international" and not self._is_international_etf(
                    etf_info["etf_name"]
                ):
                    continue
                elif category == "sector" and not self._is_sector_etf(
                    etf_info["etf_name"]
                ):
                    continue

            filtered_etfs.append(etf_info)

        # 按交易金額排序 (績效表現)
        top_by_value = sorted(
            filtered_etfs, key=lambda x: x["trading_value"], reverse=True
        )[:20]
        ranking_stats["top_performers"] = top_by_value

        # 按交易帳戶數排序 (活躍度)
        top_by_accounts = sorted(
            filtered_etfs, key=lambda x: x["trading_accounts"], reverse=True
        )[:20]
        ranking_stats["most_active"] = top_by_accounts

        # 計算績效指標
        if filtered_etfs:
            total_trading_value = sum(etf["trading_value"] for etf in filtered_etfs)
            total_trading_volume = sum(etf["trading_volume"] for etf in filtered_etfs)
            total_accounts = sum(etf["trading_accounts"] for etf in filtered_etfs)

            ranking_stats["performance_metrics"] = {
                "total_trading_value": total_trading_value,
                "total_trading_volume": total_trading_volume,
                "total_trading_accounts": total_accounts,
                "average_trading_value": total_trading_value / len(filtered_etfs),
                "average_accounts_per_etf": total_accounts / len(filtered_etfs),
            }

        # 類別分佈
        category_counts = {"domestic": 0, "international": 0, "sector": 0, "others": 0}

        for etf in filtered_etfs:
            if self._is_domestic_etf(etf["etf_name"]):
                category_counts["domestic"] += 1
            elif self._is_international_etf(etf["etf_name"]):
                category_counts["international"] += 1
            elif self._is_sector_etf(etf["etf_name"]):
                category_counts["sector"] += 1
            else:
                category_counts["others"] += 1

        ranking_stats["category_breakdown"] = category_counts

        return ranking_stats

    def _filter_etf_trading_data(self, trading_data: list) -> list:
        """從交易資料中篩選 ETF"""
        etf_trading = []
        for item in trading_data:
            stock_code = item.get("證券代號", "")
            stock_name = item.get("證券名稱", "")

            # 判斷是否為 ETF (通常代碼以 00 開頭或名稱包含 ETF)
            if (
                stock_code.startswith("00") and len(stock_code) == 4
            ) or "ETF" in stock_name:
                etf_info = {
                    "etf_code": stock_code,
                    "etf_name": stock_name,
                    "opening_price": float(item.get("開盤價", 0) or 0),
                    "closing_price": float(item.get("收盤價", 0) or 0),
                    "highest_price": float(item.get("最高價", 0) or 0),
                    "lowest_price": float(item.get("最低價", 0) or 0),
                    "trading_volume": float(item.get("成交股數", 0) or 0),
                    "trading_value": float(item.get("成交金額", 0) or 0),
                    "price_change": float(item.get("漲跌價差", 0) or 0),
                    "change_percent": self._calculate_change_percent(
                        float(item.get("漲跌價差", 0) or 0),
                        float(item.get("收盤價", 0) or 0),
                    ),
                }
                etf_trading.append(etf_info)

        return etf_trading

    def _analyze_etf_performance(self, etf_trading_data: list) -> dict:
        """分析 ETF 績效"""
        performance_stats = {
            "total_etfs": len(etf_trading_data),
            "gainers": [],
            "losers": [],
            "most_volatile": [],
            "volume_leaders": [],
            "performance_summary": {},
        }

        if not etf_trading_data:
            return performance_stats

        # 漲幅排行
        gainers = [etf for etf in etf_trading_data if etf["price_change"] > 0]
        gainers.sort(key=lambda x: x["change_percent"], reverse=True)
        performance_stats["gainers"] = gainers[:10]

        # 跌幅排行
        losers = [etf for etf in etf_trading_data if etf["price_change"] < 0]
        losers.sort(key=lambda x: x["change_percent"])
        performance_stats["losers"] = losers[:10]

        # 波動率排行 (高低價差)
        for etf in etf_trading_data:
            if etf["lowest_price"] > 0:
                etf["volatility"] = (
                    (etf["highest_price"] - etf["lowest_price"])
                    / etf["lowest_price"]
                    * 100
                )

        volatile_etfs = sorted(
            etf_trading_data, key=lambda x: x.get("volatility", 0), reverse=True
        )
        performance_stats["most_volatile"] = volatile_etfs[:10]

        # 成交量排行
        volume_leaders = sorted(
            etf_trading_data, key=lambda x: x["trading_volume"], reverse=True
        )
        performance_stats["volume_leaders"] = volume_leaders[:10]

        # 績效摘要
        total_gainers = len(gainers)
        total_losers = len(losers)
        total_unchanged = len(etf_trading_data) - total_gainers - total_losers

        performance_stats["performance_summary"] = {
            "total_gainers": total_gainers,
            "total_losers": total_losers,
            "total_unchanged": total_unchanged,
            "gainer_ratio": total_gainers / len(etf_trading_data) * 100,
            "average_change": sum(etf["change_percent"] for etf in etf_trading_data)
            / len(etf_trading_data),
        }

        return performance_stats

    def _analyze_etf_composition(self, ranking_data: dict) -> dict:
        """分析 ETF 組成"""
        composition_stats = {
            "market_concentration": {},
            "size_distribution": {},
            "category_analysis": ranking_data.get("category_breakdown", {}),
        }

        # 市場集中度分析
        top_performers = ranking_data.get("top_performers", [])
        if len(top_performers) >= 10:
            top_5_value = sum(etf["trading_value"] for etf in top_performers[:5])
            top_10_value = sum(etf["trading_value"] for etf in top_performers[:10])
            total_value = ranking_data.get("performance_metrics", {}).get(
                "total_trading_value", 1
            )

            composition_stats["market_concentration"] = {
                "top_5_share": top_5_value / total_value * 100,
                "top_10_share": top_10_value / total_value * 100,
                "concentration_level": (
                    "高度集中" if top_5_value / total_value > 0.5 else "適度分散"
                ),
            }

        return composition_stats

    def _generate_etf_recommendations(self, analysis_results: dict) -> dict:
        """生成 ETF 投資建議"""
        recommendations = {
            "investment_strategy": [],
            "risk_assessment": "",
            "suggested_etfs": [],
            "diversification_advice": [],
        }

        # 基於分析結果生成建議
        if "etf_ranking" in analysis_results:
            ranking_data = analysis_results["etf_ranking"]
            category_breakdown = ranking_data.get("category_breakdown", {})

            # 投資策略建議
            if category_breakdown.get("domestic", 0) > category_breakdown.get(
                "international", 0
            ):
                recommendations["investment_strategy"].append(
                    "市場偏向國內 ETF，考慮增加國際分散"
                )

            if category_breakdown.get("sector", 0) > 10:
                recommendations["investment_strategy"].append(
                    "行業型 ETF 豐富，可考慮主題投資"
                )

        if "performance_analysis" in analysis_results:
            performance_data = analysis_results["performance_analysis"]
            performance_summary = performance_data.get("performance_summary", {})

            # 風險評估
            gainer_ratio = performance_summary.get("gainer_ratio", 0)
            if gainer_ratio > 60:
                recommendations["risk_assessment"] = "市場情緒偏樂觀，注意估值風險"
            elif gainer_ratio < 40:
                recommendations["risk_assessment"] = "市場情緒偏謹慎，可關注價值機會"
            else:
                recommendations["risk_assessment"] = "市場情緒中性，適合均衡配置"

            # 推薦 ETF
            gainers = performance_data.get("gainers", [])[:3]
            for etf in gainers:
                recommendations["suggested_etfs"].append(
                    {
                        "code": etf["etf_code"],
                        "name": etf["etf_name"],
                        "reason": f"近期表現強勁，漲幅 {etf['change_percent']:.2f}%",
                    }
                )

        return recommendations

    def _is_domestic_etf(self, etf_name: str) -> bool:
        """判斷是否為國內 ETF"""
        domestic_keywords = ["台灣", "台股", "加權", "中小", "MSCI台灣"]
        return any(keyword in etf_name for keyword in domestic_keywords)

    def _is_international_etf(self, etf_name: str) -> bool:
        """判斷是否為國際 ETF"""
        international_keywords = [
            "美國",
            "中國",
            "日本",
            "歐洲",
            "新興",
            "全球",
            "NASDAQ",
            "S&P",
        ]
        return any(keyword in etf_name for keyword in international_keywords)

    def _is_sector_etf(self, etf_name: str) -> bool:
        """判斷是否為行業 ETF"""
        sector_keywords = [
            "科技",
            "金融",
            "生技",
            "能源",
            "REITs",
            "ESG",
            "電動車",
            "半導體",
        ]
        return any(keyword in etf_name for keyword in sector_keywords)

    def _calculate_change_percent(
        self, price_change: float, closing_price: float
    ) -> float:
        """計算漲跌幅百分比"""
        if closing_price == 0:
            return 0
        previous_price = closing_price - price_change
        if previous_price == 0:
            return 0
        return (price_change / previous_price) * 100
