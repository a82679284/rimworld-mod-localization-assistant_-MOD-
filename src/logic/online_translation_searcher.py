"""
在线翻译搜索服务
"""
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time


class OnlineTranslationSearcher:
    """在线翻译搜索器"""

    def __init__(self):
        """初始化搜索器"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_all_sources(
        self,
        term_en: str,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        从多个来源搜索翻译

        Args:
            term_en: 英文术语
            sources: 搜索来源列表(None=全部)

        Returns:
            List[Dict]: 翻译结果列表
                [{
                    'term_zh': str,
                    'source': str,
                    'confidence': float,  # 0-1
                    'note': str
                }]
        """
        if sources is None:
            sources = ['rimworld_wiki', 'steam_workshop', 'deepseek', 'baidu']

        results = []

        if 'rimworld_wiki' in sources:
            results.extend(self._search_rimworld_wiki(term_en))

        if 'steam_workshop' in sources:
            results.extend(self._search_steam_workshop(term_en))

        if 'deepseek' in sources:
            results.extend(self._search_deepseek(term_en))

        if 'baidu' in sources:
            results.extend(self._search_baidu(term_en))

        return results

    def _search_rimworld_wiki(self, term_en: str) -> List[Dict[str, str]]:
        """
        从Rimworld Wiki搜索翻译

        Args:
            term_en: 英文术语

        Returns:
            List[Dict]: 翻译结果
        """
        results = []

        try:
            # Rimworld中文Wiki搜索
            search_url = f"https://rimworldwiki.com/zh/index.php?search={term_en}"

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找搜索结果
            search_results = soup.find_all('div', class_='mw-search-result-heading')

            for result in search_results[:3]:  # 只取前3个结果
                link = result.find('a')
                if link:
                    title_zh = link.get_text(strip=True)

                    results.append({
                        'term_zh': title_zh,
                        'source': 'Rimworld Wiki',
                        'confidence': 0.9,  # Wiki结果置信度高
                        'note': f'Wiki标题: {title_zh}'
                    })

        except Exception as e:
            # 网络请求失败不影响其他来源
            pass

        return results

    def _search_steam_workshop(self, term_en: str) -> List[Dict[str, str]]:
        """
        从Steam创意工坊搜索翻译

        注意: Steam Workshop的搜索需要特殊处理,这里提供基础实现

        Args:
            term_en: 英文术语

        Returns:
            List[Dict]: 翻译结果
        """
        results = []

        try:
            # 搜索Rimworld中文汉化MOD
            search_url = (
                f"https://steamcommunity.com/workshop/browse/"
                f"?appid=294100&searchtext={term_en}+chinese"
            )

            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找MOD标题
            workshop_items = soup.find_all('div', class_='workshopItemTitle')

            for item in workshop_items[:2]:  # 只取前2个结果
                title = item.get_text(strip=True)

                # 尝试从标题提取中文翻译
                if '汉化' in title or '中文' in title:
                    results.append({
                        'term_zh': title,
                        'source': 'Steam Workshop',
                        'confidence': 0.7,
                        'note': f'来自MOD: {title}'
                    })

        except Exception:
            pass

        return results

    def _search_deepseek(self, term_en: str) -> List[Dict[str, str]]:
        """
        使用DeepSeek AI获取翻译建议

        Args:
            term_en: 英文术语

        Returns:
            List[Dict]: 翻译结果
        """
        results = []

        try:
            # 使用已有的DeepSeek翻译器
            from ..providers.deepseek_translator import DeepseekTranslator

            translator = DeepseekTranslator()

            # 构造针对性的翻译提示
            prompt = (
                f"请翻译Rimworld游戏中的术语: \"{term_en}\"\n"
                f"只需要返回最准确的中文翻译,不要解释。"
            )

            translation = translator.translate(prompt, context="Rimworld游戏术语")

            if translation and translation.strip():
                results.append({
                    'term_zh': translation.strip(),
                    'source': 'DeepSeek AI',
                    'confidence': 0.85,
                    'note': 'AI智能翻译'
                })

        except Exception:
            pass

        return results

    def _search_baidu(self, term_en: str) -> List[Dict[str, str]]:
        """
        使用百度翻译API获取翻译

        Args:
            term_en: 英文术语

        Returns:
            List[Dict]: 翻译结果
        """
        results = []

        try:
            # 百度翻译通用文本翻译(无需API key的简易版本)
            url = "https://fanyi.baidu.com/sug"
            params = {'kw': term_en}

            response = self.session.post(url, data=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            if data.get('data'):
                for item in data['data'][:2]:  # 取前2个结果
                    translation = item.get('v', '')

                    if translation:
                        results.append({
                            'term_zh': translation.split(';')[0].strip(),  # 取第一个翻译
                            'source': '百度翻译',
                            'confidence': 0.75,
                            'note': '机器翻译'
                        })

        except Exception:
            pass

        return results

    def batch_search(
        self,
        terms: List[str],
        sources: Optional[List[str]] = None,
        delay: float = 1.0
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        批量搜索多个术语

        Args:
            terms: 英文术语列表
            sources: 搜索来源
            delay: 请求间隔(秒),避免被封禁

        Returns:
            Dict[str, List[Dict]]: {术语: [翻译结果列表]}
        """
        results = {}

        for term in terms:
            results[term] = self.search_all_sources(term, sources)
            time.sleep(delay)  # 避免请求过快

        return results
