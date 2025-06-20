#!/usr/bin/env python3
"""
Stock Market Analyzer
---------------------
Comprehensive stock market data and analysis tool.
"""
import sys
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import json

class StockMarketAnalyzer:
    """Comprehensive Stock Market Analysis Tool"""
    
    def __init__(self):
        # Don't use session with yfinance due to curl_cffi compatibility issues
        pass
        
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price data
            hist = ticker.history(period="1d", interval="1m")
            current_price = hist['Close'].iloc[-1] if not hist.empty else info.get('currentPrice', 0)
            
            return {
                'success': True,
                'symbol': symbol.upper(),
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'current_price': round(current_price, 2),
                'previous_close': info.get('previousClose', 0),
                'change': round(current_price - info.get('previousClose', 0), 2),
                'change_percent': round(((current_price - info.get('previousClose', 0)) / info.get('previousClose', 1)) * 100, 2),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'beta': info.get('beta', 0),
                'eps': info.get('trailingEps', 0),
                'book_value': info.get('bookValue', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'return_on_equity': info.get('returnOnEquity', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol.upper(),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """Get historical stock data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return {
                    'success': False,
                    'symbol': symbol.upper(),
                    'error': 'No historical data found'
                }
            
            # Convert to list of dictionaries for JSON serialization
            data = []
            for date, row in hist.iterrows():
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': round(row['Open'], 2),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume'])
                })
            
            return {
                'success': True,
                'symbol': symbol.upper(),
                'period': period,
                'interval': interval,
                'data_points': len(data),
                'data': data[-50:],  # Return last 50 data points to avoid overwhelming
                'summary': {
                    'start_date': data[0]['date'] if data else None,
                    'end_date': data[-1]['date'] if data else None,
                    'highest_price': max([d['high'] for d in data]) if data else 0,
                    'lowest_price': min([d['low'] for d in data]) if data else 0,
                    'total_volume': sum([d['volume'] for d in data]) if data else 0
                }
            }
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol.upper(),
                'error': str(e)
            }
    
    def calculate_technical_indicators(self, symbol: str, period: str = "6mo") -> Dict[str, Any]:
        """Calculate technical indicators"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {
                    'success': False,
                    'symbol': symbol.upper(),
                    'error': 'No data available for technical analysis'
                }
            
            close_prices = hist['Close']
            high_prices = hist['High']
            low_prices = hist['Low']
            volume = hist['Volume']
            
            # Moving Averages
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            ema_12 = close_prices.ewm(span=12).mean().iloc[-1]
            ema_26 = close_prices.ewm(span=26).mean().iloc[-1]
            
            # RSI (Relative Strength Index)
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD
            macd_line = ema_12 - ema_26
            signal_line = close_prices.ewm(span=9).mean().iloc[-1]
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            bb_middle = close_prices.rolling(window=bb_period).mean().iloc[-1]
            bb_std_dev = close_prices.rolling(window=bb_period).std().iloc[-1]
            bb_upper = bb_middle + (bb_std_dev * bb_std)
            bb_lower = bb_middle - (bb_std_dev * bb_std)
            
            current_price = close_prices.iloc[-1]
            
            return {
                'success': True,
                'symbol': symbol.upper(),
                'current_price': round(current_price, 2),
                'moving_averages': {
                    'sma_20': round(sma_20, 2),
                    'sma_50': round(sma_50, 2),
                    'ema_12': round(ema_12, 2),
                    'ema_26': round(ema_26, 2)
                },
                'rsi': round(rsi, 2),
                'rsi_signal': 'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral',
                'macd': {
                    'macd_line': round(macd_line, 2),
                    'signal_line': round(signal_line, 2),
                    'histogram': round(macd_line - signal_line, 2)
                },
                'bollinger_bands': {
                    'upper': round(bb_upper, 2),
                    'middle': round(bb_middle, 2),
                    'lower': round(bb_lower, 2),
                    'position': 'Above Upper' if current_price > bb_upper else 'Below Lower' if current_price < bb_lower else 'Within Bands'
                },
                'trend_analysis': {
                    'price_vs_sma20': 'Above' if current_price > sma_20 else 'Below',
                    'price_vs_sma50': 'Above' if current_price > sma_50 else 'Below',
                    'sma20_vs_sma50': 'Golden Cross' if sma_20 > sma_50 else 'Death Cross'
                }
            }
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol.upper(),
                'error': str(e)
            }
    
    def screen_stocks(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Screen stocks based on criteria"""
        try:
            # Popular stock symbols for screening
            symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'AMD', 'INTC', 'CRM', 'ORCL', 'IBM', 'CSCO', 'ADBE', 'PYPL',
                'DIS', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX'
            ]
            
            results = []
            max_pe = criteria.get('max_pe_ratio', 50)
            min_market_cap = criteria.get('min_market_cap', 0)
            max_market_cap = criteria.get('max_market_cap', float('inf'))
            min_price = criteria.get('min_price', 0)
            max_price = criteria.get('max_price', float('inf'))
            
            for symbol in symbols[:10]:  # Limit to 10 stocks to avoid rate limits
                try:
                    stock_info = self.get_stock_info(symbol)
                    if stock_info['success']:
                        pe_ratio = stock_info.get('pe_ratio', 0) or 0
                        market_cap = stock_info.get('market_cap', 0) or 0
                        price = stock_info.get('current_price', 0) or 0
                        
                        # Apply filters
                        if (pe_ratio <= max_pe and 
                            min_market_cap <= market_cap <= max_market_cap and
                            min_price <= price <= max_price):
                            
                            results.append({
                                'symbol': symbol,
                                'company_name': stock_info['company_name'],
                                'price': price,
                                'change_percent': stock_info['change_percent'],
                                'pe_ratio': pe_ratio,
                                'market_cap': market_cap,
                                'volume': stock_info['volume']
                            })
                except:
                    continue
            
            # Sort by market cap (descending)
            results.sort(key=lambda x: x['market_cap'], reverse=True)
            
            return {
                'success': True,
                'criteria': criteria,
                'total_screened': len(symbols),
                'matches_found': len(results),
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices data"""
        try:
            indices = {
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC',
                'Dow Jones': '^DJI',
                'Russell 2000': '^RUT',
                'VIX': '^VIX'
            }
            
            results = {}
            for name, symbol in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                        change = current - previous
                        change_percent = (change / previous) * 100 if previous != 0 else 0
                        
                        results[name] = {
                            'symbol': symbol,
                            'current_value': round(current, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                        }
                except:
                    results[name] = {'error': 'Data not available'}
            
            return {
                'success': True,
                'indices': results,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_portfolio(self, holdings: List[Dict[str, Union[str, float]]]) -> Dict[str, Any]:
        """Analyze a portfolio of stocks"""
        try:
            portfolio_data = []
            total_value = 0
            total_cost = 0
            
            for holding in holdings:
                symbol = holding['symbol']
                shares = holding['shares']
                cost_basis = holding.get('cost_basis', 0)
                
                stock_info = self.get_stock_info(symbol)
                if stock_info['success']:
                    current_price = stock_info['current_price']
                    current_value = shares * current_price
                    cost_value = shares * cost_basis if cost_basis > 0 else current_value
                    gain_loss = current_value - cost_value
                    gain_loss_percent = (gain_loss / cost_value * 100) if cost_value > 0 else 0
                    
                    portfolio_data.append({
                        'symbol': symbol,
                        'company_name': stock_info['company_name'],
                        'shares': shares,
                        'cost_basis': cost_basis,
                        'current_price': current_price,
                        'current_value': round(current_value, 2),
                        'cost_value': round(cost_value, 2),
                        'gain_loss': round(gain_loss, 2),
                        'gain_loss_percent': round(gain_loss_percent, 2),
                        'weight': 0  # Will calculate after total
                    })
                    
                    total_value += current_value
                    total_cost += cost_value
            
            # Calculate weights
            for holding in portfolio_data:
                holding['weight'] = round((holding['current_value'] / total_value * 100), 2) if total_value > 0 else 0
            
            total_gain_loss = total_value - total_cost
            total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
            
            return {
                'success': True,
                'portfolio_summary': {
                    'total_value': round(total_value, 2),
                    'total_cost': round(total_cost, 2),
                    'total_gain_loss': round(total_gain_loss, 2),
                    'total_gain_loss_percent': round(total_gain_loss_percent, 2),
                    'number_of_holdings': len(portfolio_data)
                },
                'holdings': portfolio_data,
                'top_performers': sorted(portfolio_data, key=lambda x: x['gain_loss_percent'], reverse=True)[:3],
                'worst_performers': sorted(portfolio_data, key=lambda x: x['gain_loss_percent'])[:3]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_crypto_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get cryptocurrency data"""
        try:
            if symbols is None:
                symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD']
            
            crypto_data = []
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                        change = current - previous
                        change_percent = (change / previous) * 100 if previous != 0 else 0
                        
                        crypto_data.append({
                            'symbol': symbol,
                            'name': symbol.replace('-USD', ''),
                            'current_price': round(current, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                        })
                except:
                    continue
            
            return {
                'success': True,
                'cryptocurrencies': crypto_data,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

def format_stock_report(stock_data: Dict[str, Any]) -> str:
    """Format stock data into a readable report"""
    if not stock_data['success']:
        return f"❌ Error getting data for {stock_data['symbol']}: {stock_data.get('error', 'Unknown error')}"
    
    report = []
    report.append(f"📈 {stock_data['company_name']} ({stock_data['symbol']})")
    report.append("=" * 50)
    
    # Price information
    change_emoji = "📈" if stock_data['change'] >= 0 else "📉"
    report.append(f"💰 Current Price: ${stock_data['current_price']}")
    report.append(f"{change_emoji} Change: ${stock_data['change']} ({stock_data['change_percent']}%)")
    report.append(f"📊 Volume: {stock_data['volume']:,}")
    
    # Company metrics
    report.append(f"\n🏢 Company Metrics:")
    report.append(f"   Sector: {stock_data['sector']}")
    report.append(f"   Industry: {stock_data['industry']}")
    report.append(f"   Market Cap: ${stock_data['market_cap']:,}")
    report.append(f"   P/E Ratio: {stock_data['pe_ratio']}")
    report.append(f"   Beta: {stock_data['beta']}")
    
    # 52-week range
    report.append(f"\n📅 52-Week Range:")
    report.append(f"   High: ${stock_data['fifty_two_week_high']}")
    report.append(f"   Low: ${stock_data['fifty_two_week_low']}")
    
    return "\n".join(report)

# For testing
if __name__ == "__main__":
    analyzer = StockMarketAnalyzer()
    
    print("🚀 Testing Stock Market Analyzer...")
    
    # Test stock info
    print("\n📊 Getting AAPL stock info...")
    aapl_info = analyzer.get_stock_info("AAPL")
    print(format_stock_report(aapl_info))
    
    # Test technical indicators
    print("\n🔍 Getting technical indicators...")
    tech_analysis = analyzer.calculate_technical_indicators("AAPL")
    if tech_analysis['success']:
        print(f"RSI: {tech_analysis['rsi']} ({tech_analysis['rsi_signal']})")
        print(f"Price vs SMA20: {tech_analysis['trend_analysis']['price_vs_sma20']}")
    
    # Test market indices
    print("\n📈 Getting market indices...")
    indices = analyzer.get_market_indices()
    if indices['success']:
        for name, data in indices['indices'].items():
            if 'error' not in data:
                print(f"{name}: {data['current_value']} ({data['change_percent']:+.2f}%)") 