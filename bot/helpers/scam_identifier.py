# scam_identifier.py
import re
from typing import Dict, List

class ScamIdentifier:
    def __init__(self):
        # Patterns commonly found in crypto giveaway scams
        self.patterns = {
            "giveaway_amount": [
                r'\$[0-9,]+\.?[0-9]*\s*(bonus|reward|giveaway|free)',
                r'(bonus|reward|giveaway|free)\s*\$[0-9,]+\.?[0-9]*',
                r'giving away \$[0-9,]+\.?[0-9]*',
                r'claim your \$[0-9,]+\.?[0-9]*'
            ],
            "promo_code": [
                r'promo code:?\s*[A-Z0-9]+',
                r'code:?\s*[A-Z0-9]+',
                r'enter.*code',
                r'BET'  # Specific code from the example
            ],
            "crypto_terms": [
                r'cryptocurrency',
                r'crypto',
                r'USDT',
                r'Tether',
                r'bitcoin',
                r'ethereum',
                r'wallet',
                r'blockchain',
                r'transfer',
                r'withdraw'
            ],
            "urgency": [
                r'deleted.*hour',
                r'limited time',
                r'fastest',
                r'don\'t miss',
                r'only.*people',
                r'immediately',
                r'urgent'
            ],
            "celebrity_impersonation": [
                r'MrBeast',
                r'Kai Cenat',
                r'Elon Musk',
                r'Vitalik Buterin',
                r'CZ',
                r'Snoop Dogg',
                r'Drake'
            ],
            "casino_gambling": [
                r'casino',
                r'bet',
                r'gambling',
                r'poker',
                r'roulette',
                r'slots'
            ],
            "withdrawal_process": [
                r'withdraw.*bonus',
                r'withdrawal.*success',
                r'wallet address',
                r'enter.*wallet',
                r'network fee',
                r'TRX'
            ],
            "suspicious_domain": [
                r'fuzawin\.com',
                r'vyro',
                r'\.xyz',
                r'\.top',
                r'\.club',
                r'\.win'
            ],
            "promotional_claims": [
                r'new.*launch',
                r'announce.*launch',
                r'exciting.*event',
                r'celebrate',
                r'big event'
            ]
        }
        
        # High-risk combinations that strongly indicate scam
        self.high_risk_combinations = [
            (r'giveaway.*crypto', r'wallet'),
            (r'MrBeast.*casino', r'bonus'),
            (r'promo.*code', r'withdraw'),
            (r'free.*money', r'crypto'),
            (r'impersonation', r'wallet')
        ]
    
    def _extract_amounts(self, text: str) -> List[float]:
        """Extract monetary amounts from text"""
        amounts = []
        # Find dollar amounts
        dollar_pattern = r'\$([0-9,]+\.?[0-9]*)'
        matches = re.findall(dollar_pattern, text)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                amounts.append(amount)
            except:
                continue
        
        # Find amounts with words
        amount_pattern = r'([0-9,]+\.?[0-9]*)\s*(USDT|dollars?|USD)'
        matches = re.findall(amount_pattern, text)
        for match in matches:
            try:
                amount = float(match[0].replace(',', ''))
                amounts.append(amount)
            except:
                continue
                
        return amounts
    
    def _check_patterns(self, text: str) -> Dict[str, float]:
        """Check all patterns and return scores"""
        scores = {}
        text_lower = text.lower()
        
        for category, patterns in self.patterns.items():
            category_score = 0.0
            matches_found = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches_found += 1
            
            if matches_found > 0:
                category_score = min(1.0, matches_found / len(patterns))
            
            scores[category] = category_score
        
        return scores
    
    def _check_high_risk_combinations(self, text: str) -> float:
        """Check for high-risk combinations of scam indicators"""
        risk_score = 0.0
        combinations_found = 0
        
        for combo in self.high_risk_combinations:
            pattern1, pattern2 = combo
            if re.search(pattern1, text, re.IGNORECASE) and re.search(pattern2, text, re.IGNORECASE):
                combinations_found += 1
        
        if combinations_found > 0:
            risk_score = min(1.0, combinations_found / len(self.high_risk_combinations))
        
        return risk_score
    
    def _check_suspicious_numbers(self, text: str) -> float:
        """Check for suspicious patterns in numbers"""
        amounts = self._extract_amounts(text)
        
        if not amounts:
            return 0.0
        
        # Check for large round numbers (common in scams)
        suspicious = 0
        for amount in amounts:
            # Amounts like 5600, 5000, 10000 etc.
            if amount >= 1000 and amount % 100 == 0:
                suspicious += 1
            # Very large amounts
            if amount >= 10000:
                suspicious += 1
        
        if suspicious > 0:
            return min(1.0, suspicious / len(amounts))
        
        return 0.0
    
    def _check_social_media_indicators(self, text: str) -> float:
        """Check for social media impersonation indicators"""
        indicators = 0
        total = 4  # Number of indicators we check
        
        # Check for social media handles
        if re.search(r'@[A-Za-z0-9_]+', text):
            indicators += 1
        
        # Check for follower/following mentions
        if re.search(r'(followers|following|subscribers|posts)', text, re.IGNORECASE):
            indicators += 1
        
        # Check for social media platforms
        if re.search(r'(Twitter|YouTube|Instagram|TikTok)', text, re.IGNORECASE):
            indicators += 1
        
        # Check for pinned post indicators
        if re.search(r'(pinned|subs|replies|highlights)', text, re.IGNORECASE):
            indicators += 1
        
        return indicators / total
    
    def identify_scam(self, text: str) -> float:
        """
        Main function to identify if text is a crypto scam.
        Returns a scam score between 0 and 1.
        """
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Get pattern scores
        pattern_scores = self._check_patterns(text)
        
        # Calculate weighted average of pattern scores
        weights = {
            "giveaway_amount": 0.25,
            "promo_code": 0.20,
            "crypto_terms": 0.10,
            "urgency": 0.15,
            "celebrity_impersonation": 0.15,
            "casino_gambling": 0.05,
            "withdrawal_process": 0.05,
            "suspicious_domain": 0.03,
            "promotional_claims": 0.02
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for category, score in pattern_scores.items():
            weight = weights.get(category, 0.05)
            weighted_score += score * weight
            total_weight += weight
        
        normalized_pattern_score = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Get additional risk factors
        combination_score = self._check_high_risk_combinations(text)
        suspicious_numbers_score = self._check_suspicious_numbers(text)
        social_media_score = self._check_social_media_indicators(text)
        
        # Combine all scores with weights
        final_score = (
            normalized_pattern_score * 0.70 +
            combination_score * 0.50 +
            suspicious_numbers_score * 0.30 +
            social_media_score * 0.20
        )
        
        # Ensure score is between 0 and 1
        final_score = max(0.0, min(1.0, final_score))
        
        return final_score


# Convenience function for easy import
def identify_scam(text: str) -> float:
    """
    Convenience function to identify if text is a crypto scam.
    Returns a scam score between 0 and 1.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        float: Scam score between 0 and 1
    """
    identifier = ScamIdentifier()
    return identifier.identify_scam(text.lower().strip())