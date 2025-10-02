"""
進階股息分析工具
"""

from typing import Any

from ...api.openapi_client import OpenAPIClient
from ..base import ToolBase


class DividendAnalysisTool(ToolBase):
    """
    股息分析工具。

    提供股息分配、殖利率分析、股息政策等深度分析服務。
    """

    def __init__(self):
        super().__init__("dividend_analysis")
        self.openapi_client = OpenAPIClient()

    async def execute(
        self, symbol: str = "", analysis_type: str = "comprehensive", **kwargs
    ) -> dict[str, Any]:
        """
        執行股息分析。

        Args:
            symbol: 股票代碼 (可選，留空則分析全市場)
            analysis_type: 分析類型 (comprehensive, distribution, yield, policy)

        Returns:
            包含股息分析結果的字典
        """
        try:
            self.logger.info(f"執行股息分析: symbol={symbol}, type={analysis_type}")

            analysis_results = {}

            # 取得股息分配資料
            dividend_data = await self.openapi_client.get_data("/opendata/t187ap45_L")
            if not dividend_data:
                return self._error_response("無法取得股息分配資料")

            # 取得 P/E 比和殖利率資料
            pe_dividend_data = await self.openapi_client.get_data(
                "/exchangeReport/BWIBBU_ALL"
            )

            # 如果指定股票代碼，過濾資料
            if symbol:
                dividend_data = [
                    item
                    for item in dividend_data
                    if symbol in str(item.get("公司代號", ""))
                ]
                if pe_dividend_data:
                    pe_dividend_data = [
                        item
                        for item in pe_dividend_data
                        if symbol in str(item.get("證券代號", ""))
                    ]

            if analysis_type in ["comprehensive", "distribution"]:
                analysis_results["dividend_distribution"] = (
                    self._analyze_dividend_distribution(dividend_data)
                )

            if analysis_type in ["comprehensive", "yield"] and pe_dividend_data:
                analysis_results["yield_analysis"] = self._analyze_dividend_yield(
                    pe_dividend_data
                )

            if analysis_type in ["comprehensive", "policy"]:
                analysis_results["dividend_policy"] = self._analyze_dividend_policy(
                    dividend_data
                )

            # 生成綜合統計
            if analysis_type == "comprehensive":
                analysis_results["summary"] = self._generate_dividend_summary(
                    dividend_data, pe_dividend_data
                )

            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "analysis_type": analysis_type,
                    "total_companies": len(dividend_data),
                    "analysis_results": analysis_results,
                },
            }

        except Exception as e:
            self.logger.error(f"股息分析失敗: {e}")
            return self._error_response(str(e))

    def _analyze_dividend_distribution(self, dividend_data: list) -> dict:
        """分析股息分配情況"""
        distribution_stats = {
            "total_companies": len(dividend_data),
            "cash_dividend_companies": 0,
            "stock_dividend_companies": 0,
            "both_dividend_companies": 0,
            "average_cash_dividend": 0,
            "average_stock_dividend": 0,
            "high_dividend_companies": [],
            "dividend_details": [],
        }

        total_cash = 0
        total_stock = 0
        cash_count = 0
        stock_count = 0

        for item in dividend_data[:100]:  # 限制分析數量
            cash_dividend = float(item.get("現金股利", 0) or 0)
            stock_dividend = float(item.get("股票股利", 0) or 0)

            company_info = {
                "company_code": item.get("公司代號", ""),
                "company_name": item.get("公司名稱", ""),
                "cash_dividend": cash_dividend,
                "stock_dividend": stock_dividend,
                "ex_dividend_date": item.get("除息日", ""),
                "payment_date": item.get("發放日", ""),
            }
            distribution_stats["dividend_details"].append(company_info)

            if cash_dividend > 0:
                distribution_stats["cash_dividend_companies"] += 1
                total_cash += cash_dividend
                cash_count += 1

            if stock_dividend > 0:
                distribution_stats["stock_dividend_companies"] += 1
                total_stock += stock_dividend
                stock_count += 1

            if cash_dividend > 0 and stock_dividend > 0:
                distribution_stats["both_dividend_companies"] += 1

            # 高股息公司 (現金股利 > 3元)
            if cash_dividend > 3:
                distribution_stats["high_dividend_companies"].append(company_info)

        if cash_count > 0:
            distribution_stats["average_cash_dividend"] = total_cash / cash_count

        if stock_count > 0:
            distribution_stats["average_stock_dividend"] = total_stock / stock_count

        return distribution_stats

    def _analyze_dividend_yield(self, pe_data: list) -> dict:
        """分析殖利率"""
        yield_stats = {
            "average_yield": 0,
            "high_yield_stocks": [],
            "low_yield_stocks": [],
            "yield_distribution": {
                "0-2%": 0,
                "2-4%": 0,
                "4-6%": 0,
                "6-8%": 0,
                "8%+": 0,
            },
        }

        total_yield = 0
        yield_count = 0

        for item in pe_data[:100]:  # 限制分析數量
            dividend_yield = float(item.get("殖利率", 0) or 0)

            if dividend_yield > 0:
                total_yield += dividend_yield
                yield_count += 1

                stock_info = {
                    "symbol": item.get("證券代號", ""),
                    "name": item.get("證券名稱", ""),
                    "dividend_yield": dividend_yield,
                    "pe_ratio": item.get("本益比", 0),
                }

                # 分類殖利率
                if dividend_yield < 2:
                    yield_stats["yield_distribution"]["0-2%"] += 1
                elif dividend_yield < 4:
                    yield_stats["yield_distribution"]["2-4%"] += 1
                elif dividend_yield < 6:
                    yield_stats["yield_distribution"]["4-6%"] += 1
                elif dividend_yield < 8:
                    yield_stats["yield_distribution"]["6-8%"] += 1
                else:
                    yield_stats["yield_distribution"]["8%+"] += 1

                # 高殖利率股票 (>6%)
                if dividend_yield > 6:
                    yield_stats["high_yield_stocks"].append(stock_info)

        if yield_count > 0:
            yield_stats["average_yield"] = total_yield / yield_count

        # 排序高殖利率股票
        yield_stats["high_yield_stocks"].sort(
            key=lambda x: x["dividend_yield"], reverse=True
        )

        return yield_stats

    def _analyze_dividend_policy(self, dividend_data: list) -> dict:
        """分析股息政策"""
        policy_stats = {
            "stable_dividend_companies": 0,
            "increasing_dividend_companies": 0,
            "decreasing_dividend_companies": 0,
            "policy_trends": [],
            "dividend_consistency": {},
        }

        # 這裡需要歷史資料來分析趨勢，目前僅提供當期分析
        for item in dividend_data[:50]:
            cash_dividend = float(item.get("現金股利", 0) or 0)

            policy_info = {
                "company_code": item.get("公司代號", ""),
                "company_name": item.get("公司名稱", ""),
                "current_cash_dividend": cash_dividend,
                "policy_type": "穩定配息" if cash_dividend > 0 else "無配息",
            }
            policy_stats["policy_trends"].append(policy_info)

            if cash_dividend > 0:
                policy_stats["stable_dividend_companies"] += 1

        return policy_stats

    def _generate_dividend_summary(self, dividend_data: list, pe_data: list) -> dict:
        """生成股息分析摘要"""
        summary = {
            "market_overview": {
                "total_dividend_companies": len(dividend_data),
                "dividend_paying_ratio": 0,
                "market_average_yield": 0,
            },
            "investment_insights": [],
            "recommendations": [],
        }

        # 計算配息公司比例
        paying_companies = len(
            [item for item in dividend_data if float(item.get("現金股利", 0) or 0) > 0]
        )

        if len(dividend_data) > 0:
            summary["market_overview"]["dividend_paying_ratio"] = (
                paying_companies / len(dividend_data) * 100
            )

        # 計算市場平均殖利率
        if pe_data:
            total_yield = sum(float(item.get("殖利率", 0) or 0) for item in pe_data)
            if len(pe_data) > 0:
                summary["market_overview"]["market_average_yield"] = total_yield / len(
                    pe_data
                )

        # 投資洞察
        summary["investment_insights"] = [
            f"市場中 {paying_companies} 家公司有配發現金股利",
            f"配息公司比例為 {summary['market_overview']['dividend_paying_ratio']:.1f}%",
            f"市場平均殖利率為 {summary['market_overview']['market_average_yield']:.2f}%",
        ]

        return summary
