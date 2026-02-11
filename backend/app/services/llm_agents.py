"""
LLM Agents for Iridology Analysis

Three specialized agents based on the methodologies of:
1. Ignaz von Peczely (1826-1911)
2. Bernard Jensen (1908-2001)
3. Dr. Robert Morse, ND
"""

import os
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional
from anthropic import Anthropic


def load_reference_charts() -> Dict[str, str]:
    """Load reference chart images as base64 for Claude vision."""
    charts_dir = Path(__file__).parent.parent / "knowledge" / "reference_charts"
    charts = {}

    if charts_dir.exists():
        for img_path in charts_dir.glob("*.jpg"):
            with open(img_path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode("utf-8")
                charts[img_path.stem] = img_data

    return charts


# Load reference charts once at module level
REFERENCE_CHARTS = load_reference_charts()


class BaseIridologyAgent:
    """Base class for iridology analysis agents."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=self.api_key)
        self.methodology = self._load_methodology()
        self.reference_charts = REFERENCE_CHARTS

    def _load_methodology(self) -> str:
        """Load the methodology file for this agent. Override in subclass."""
        raise NotImplementedError

    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent. Override in subclass."""
        raise NotImplementedError

    def _get_reference_chart_keys(self) -> List[str]:
        """Return which reference charts this agent should use. Override in subclass."""
        return list(self.reference_charts.keys())[:2]  # Default: use first 2 charts

    def analyze(self, left_iris_features: Optional[Dict], right_iris_features: Optional[Dict],
                patient_name: str, notes: Optional[str] = None,
                left_iris_image: Optional[bytes] = None, right_iris_image: Optional[bytes] = None) -> Dict:
        """Perform iridology analysis using Claude with vision."""

        # Build multi-modal content with images
        content = self._build_analysis_content(
            left_iris_features, right_iris_features, patient_name, notes,
            left_iris_image, right_iris_image
        )

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            system=self._get_system_prompt(),
            messages=[
                {"role": "user", "content": content}
            ]
        )

        # Parse the response
        return self._parse_response(response.content[0].text)

    def _build_analysis_content(self, left_features: Optional[Dict], right_features: Optional[Dict],
                                 patient_name: str, notes: Optional[str],
                                 left_image: Optional[bytes], right_image: Optional[bytes]) -> List[Dict]:
        """Build multi-modal content including images and text."""
        content = []

        # Add reference charts first
        chart_keys = self._get_reference_chart_keys()
        for key in chart_keys:
            if key in self.reference_charts:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": self.reference_charts[key]
                    }
                })

        if chart_keys:
            content.append({
                "type": "text",
                "text": """Above are iridology reference charts. You MUST use these charts to perform zone-by-zone analysis:

CRITICAL OVERLAY INSTRUCTIONS:
1. Mentally overlay the reference chart onto each patient iris image
2. Align the pupil center of the chart with the pupil center of the patient's iris
3. Match the 12 o'clock position (top) of both chart and iris
4. Scale the chart zones to match the patient's iris size
5. For each clock position (1-12 o'clock), identify which organ zone it corresponds to on the chart
6. Examine the patient's iris at that exact zone and note any markings, discolorations, or signs
7. The RIGHT iris chart maps to the RIGHT side of the body, LEFT iris to LEFT side of body

Use the reference charts as a transparent overlay guide - every finding should reference the specific clock position and the corresponding organ zone from the chart."""
            })

        # Add patient iris images if provided
        if right_image:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(right_image).decode("utf-8")
                }
            })
            content.append({"type": "text", "text": """RIGHT IRIS (OD) - Patient's right eye image above.

Overlay the RIGHT EYE reference chart onto this iris:
- Align pupil centers and 12 o'clock positions
- Systematically examine each clock position (12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
- At each position, identify the organ zone from the chart and note what you observe in the patient's iris
- Pay special attention to: lacunae, crypts, pigmentation, fiber density, nerve rings, and coloration changes"""})

        if left_image:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(left_image).decode("utf-8")
                }
            })
            content.append({"type": "text", "text": """LEFT IRIS (OS) - Patient's left eye image above.

Overlay the LEFT EYE reference chart onto this iris:
- Align pupil centers and 12 o'clock positions
- Systematically examine each clock position (12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
- At each position, identify the organ zone from the chart and note what you observe in the patient's iris
- Pay special attention to: lacunae, crypts, pigmentation, fiber density, nerve rings, and coloration changes"""})

        # Add the text analysis request
        content.append({
            "type": "text",
            "text": self._build_analysis_request(left_features, right_features, patient_name, notes)
        })

        return content

    def _build_analysis_request(self, left_features: Optional[Dict], right_features: Optional[Dict],
                                 patient_name: str, notes: Optional[str]) -> str:
        """Build the analysis request message."""
        request = f"""Please analyze the following iris data for patient: {patient_name}

"""
        if notes:
            request += f"Additional notes from practitioner: {notes}\n\n"

        if right_features:
            request += "RIGHT IRIS FEATURES:\n"
            request += json.dumps(right_features, indent=2)
            request += "\n\n"

        if left_features:
            request += "LEFT IRIS FEATURES:\n"
            request += json.dumps(left_features, indent=2)
            request += "\n\n"

        request += """
ANALYSIS INSTRUCTIONS:
Using the reference chart as an overlay on the patient's iris images, perform a systematic zone-by-zone analysis:

1. For each clock position (12 o'clock through 11 o'clock), identify:
   - The organ/system zone from the reference chart at that position
   - What you observe in the patient's iris at that exact location
   - Any significant markings (lacunae, crypts, pigmentation, radii solaris, nerve rings, etc.)

2. Examine the concentric rings from center outward:
   - Pupillary zone (stomach/digestive)
   - Collarette/Autonomic Nerve Wreath
   - Ciliary zone (major organs)
   - Lymphatic/peripheral zone

Based on your methodology and the chart-overlay analysis, please provide:
1. Key findings (list observations with specific clock positions and corresponding organ zones from the chart)
2. Organ correlations (map each finding to the organ zone identified on the reference chart)
3. Recommendations (lifestyle, nutritional, or other suggestions based on findings)
4. Confidence notes (any limitations or caveats in your analysis)

Format your response as JSON with these keys: findings, organ_correlations, recommendations, confidence_notes
"""
        return request

    def _parse_response(self, response_text: str) -> Dict:
        """Parse the Claude response into structured data."""
        # Try to extract JSON from the response
        try:
            # Look for JSON block in response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")

            parsed = json.loads(json_str)
            return {
                "findings": parsed.get("findings", []),
                "organ_correlations": parsed.get("organ_correlations", {}),
                "recommendations": parsed.get("recommendations", []),
                "confidence_notes": parsed.get("confidence_notes", "Analysis based on available iris data.")
            }
        except (json.JSONDecodeError, ValueError):
            # Fallback: return raw response as findings
            return {
                "findings": [response_text],
                "organ_correlations": {},
                "recommendations": [],
                "confidence_notes": "Response format was non-standard; raw analysis provided."
            }


class PeczelyAgent(BaseIridologyAgent):
    """Agent based on Ignaz von Peczely's methodology."""

    def _load_methodology(self) -> str:
        path = Path(__file__).parent.parent / "knowledge" / "peczely_methodology.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_reference_chart_keys(self) -> List[str]:
        # Use the general iridology chart and seven zones chart
        return ["81e5Oz3mPRL._AC_SL1500_", "il_1588xN.6184987103_2pch"]

    def _get_system_prompt(self) -> str:
        return f"""You are an iridology analysis system based on the methodology of Dr. Ignaz von Peczely (1826-1911), the father of modern iridology.

## Your Methodology:
{self.methodology}

## Your Analysis Approach:
1. Focus on the historical, foundational approach to iridology
2. Use Peczely's original organ-zone mapping based on his iris chart
3. Distinguish between acute (white/light) and chronic (dark) signs
4. Consider the iris as a map reflecting organ conditions
5. Look for healing signs (lightening of previously dark areas)
6. Apply Peczely's systematic clock-face examination method

## Important Guidelines:
- You are providing observations based on traditional iridology, not medical diagnoses
- Always emphasize that iris signs show predispositions and conditions, not specific diseases
- Focus on simple, direct correlations as Peczely practiced
- Note that the right iris primarily reflects the right side of the body, and vice versa
- Acknowledge limitations in what can be determined from iris analysis alone

Provide your analysis in a structured, professional manner while honoring Peczely's historical approach to iridology."""


class JensenAgent(BaseIridologyAgent):
    """Agent based on Bernard Jensen's methodology."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.iris_chart = self._load_iris_chart()

    def _load_methodology(self) -> str:
        path = Path(__file__).parent.parent / "knowledge" / "jensen_methodology.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_iris_chart(self) -> Dict:
        path = Path(__file__).parent.parent / "knowledge" / "jensen_iris_chart.json"
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_reference_chart_keys(self) -> List[str]:
        # Use Bernard Jensen's official chart and the detailed iridiagnosis chart
        return ["Screenshot 2026-02-08 124523", "il_1588xN.6136875798_1k0l"]

    def _get_system_prompt(self) -> str:
        return f"""You are an iridology analysis system based on the methodology of Dr. Bernard Jensen (1908-2001), who dedicated over 75 years to iridology practice and research.

## Your Methodology:
{self.methodology}

## Jensen's 96-Zone Iris Chart Reference:
{json.dumps(self.iris_chart, indent=2)}

## Your Analysis Approach:
1. Determine constitutional type (Blue/Lymphatic, Brown/Hematogenic, Mixed/Biliary, or Hazel)
2. Assess fiber density (Silk, Linen, Hessian, or Net)
3. Evaluate the Autonomic Nerve Wreath (position, regularity, condition)
4. Systematically examine each of the 96 zones using Jensen's chart
5. Note acute vs. chronic markings using Jensen's 7-stage scale
6. Identify lacunae, crypts, nerve rings, radii solaris, and other specific signs
7. Check peripheral signs (lymphatic rosary, scurf rim, arcus senilis)
8. Correlate bilateral findings between both irises

## Important Guidelines:
- You are providing constitutional analysis, not medical diagnoses
- Use Jensen's comprehensive approach examining all aspects of iris structure
- Relate findings to Jensen's nutritional philosophy when making recommendations
- Consider the fiber density as indicator of overall constitutional strength
- Pay special attention to the Autonomic Nerve Wreath as Jensen considered it most important
- Note healing signs and regenerative potential

Provide thorough, detailed analysis honoring Jensen's 75 years of clinical observation and research."""


class MorseAgent(BaseIridologyAgent):
    """Agent based on Dr. Robert Morse's methodology."""

    def _load_methodology(self) -> str:
        path = Path(__file__).parent.parent / "knowledge" / "morse_methodology.md"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _get_reference_chart_keys(self) -> List[str]:
        # Use the reflexology cards which show organ zones clearly
        return ["il_1588xN.7613594020_fu4u", "il_1588xN.7661532365_kcyc"]

    def _get_system_prompt(self) -> str:
        return f"""You are an iridology analysis system based on the methodology of Dr. Robert Morse, ND, a naturopathic doctor with over 50 years of practice specializing in detoxification and cellular regeneration.

## Your Methodology:
{self.methodology}

## Your Analysis Approach:
1. Assess the lymphatic system as primary focus - look for congestion signs throughout
2. Carefully evaluate the kidney/adrenal complex at 6 o'clock in both irises
3. Note nerve rings and their correlation with adrenal/stress patterns
4. Identify genetic weaknesses shown by lacunae and their locations
5. Assess overall tissue state (acute, subacute, chronic, degenerative)
6. Evaluate the "terrain" - overall cloudiness vs. clarity
7. Consider the glandular weakness pattern (pituitary, thyroid, adrenals, reproductive)

## Morse's Key Principles:
- The lymphatic system is the body's "sewer system" - congestion here underlies most conditions
- "If the kidneys aren't filtering, the lymph backs up throughout the entire body"
- Acidosis is at the root of disease conditions
- Fruits and herbs are the most powerful tools for cellular regeneration
- The body is a self-healing machine when given proper conditions
- Genetics load the gun, but lifestyle pulls the trigger

## Important Guidelines:
- You are providing naturopathic observations, not medical diagnoses
- Emphasize Morse's focus on lymphatic health and kidney filtration
- Relate findings to detoxification and cellular regeneration potential
- Make recommendations aligned with Morse's fruit-based, herbal approach
- Note genetic predispositions shown in the iris as areas requiring attention
- Consider the relationship between nervous system signs and adrenal health

Provide analysis from a naturopathic, regenerative perspective as Dr. Morse would approach it."""


class IridologyAgentManager:
    """Manages all three iridology agents and coordinates analysis."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._peczely_agent = None
        self._jensen_agent = None
        self._morse_agent = None

    @property
    def peczely_agent(self) -> PeczelyAgent:
        if self._peczely_agent is None:
            self._peczely_agent = PeczelyAgent(self.api_key)
        return self._peczely_agent

    @property
    def jensen_agent(self) -> JensenAgent:
        if self._jensen_agent is None:
            self._jensen_agent = JensenAgent(self.api_key)
        return self._jensen_agent

    @property
    def morse_agent(self) -> MorseAgent:
        if self._morse_agent is None:
            self._morse_agent = MorseAgent(self.api_key)
        return self._morse_agent

    async def analyze_all(self, left_iris_features: Optional[Dict],
                          right_iris_features: Optional[Dict],
                          patient_name: str,
                          notes: Optional[str] = None,
                          left_iris_image: Optional[bytes] = None,
                          right_iris_image: Optional[bytes] = None) -> Dict:
        """Run analysis with all three doctor agents."""

        results = {
            "peczely": {
                "doctor_name": "Ignaz von Peczely",
                "methodology": "Historical/Foundational Iridology (1880s)",
                **self.peczely_agent.analyze(left_iris_features, right_iris_features, patient_name, notes,
                                              left_iris_image, right_iris_image)
            },
            "jensen": {
                "doctor_name": "Bernard Jensen",
                "methodology": "Comprehensive Constitutional Analysis (75 years of research)",
                **self.jensen_agent.analyze(left_iris_features, right_iris_features, patient_name, notes,
                                             left_iris_image, right_iris_image)
            },
            "morse": {
                "doctor_name": "Dr. Robert Morse, ND",
                "methodology": "Naturopathic/Detoxification Approach (50+ years of practice)",
                **self.morse_agent.analyze(left_iris_features, right_iris_features, patient_name, notes,
                                            left_iris_image, right_iris_image)
            }
        }

        return results

    def analyze_single(self, doctor: str, left_iris_features: Optional[Dict],
                       right_iris_features: Optional[Dict],
                       patient_name: str, notes: Optional[str] = None) -> Dict:
        """Run analysis with a single doctor agent."""

        doctor_lower = doctor.lower()

        if doctor_lower in ["peczely", "ignaz"]:
            agent = self.peczely_agent
            doctor_name = "Ignaz von Peczely"
            methodology = "Historical/Foundational Iridology (1880s)"
        elif doctor_lower in ["jensen", "bernard"]:
            agent = self.jensen_agent
            doctor_name = "Bernard Jensen"
            methodology = "Comprehensive Constitutional Analysis (75 years of research)"
        elif doctor_lower in ["morse", "robert"]:
            agent = self.morse_agent
            doctor_name = "Dr. Robert Morse, ND"
            methodology = "Naturopathic/Detoxification Approach (50+ years of practice)"
        else:
            raise ValueError(f"Unknown doctor: {doctor}. Use 'peczely', 'jensen', or 'morse'.")

        return {
            "doctor_name": doctor_name,
            "methodology": methodology,
            **agent.analyze(left_iris_features, right_iris_features, patient_name, notes)
        }
