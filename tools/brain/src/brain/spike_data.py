"""SMOKE-TEST data for the laya spike. Hand-written for this repository: NOT UPSC PYQs, NOT copied from any
paper, and far too small to be a benchmark (36 and 30 items). It only checks that the pipeline runs and gives a
first, rough sense of zero-shot behaviour."""
from __future__ import annotations

MAX_OPTIONS = 20  # laya model card: keep `choice` questions under ~20 options (shared 256-token head budget)

SUBJECTS = {
    "polity": "constitution, parliament, elections, federalism, judiciary, governance",
    "economy": "money, banking, inflation, taxation, budget, trade, growth",
    "history": "ancient, medieval and modern Indian history and freedom struggle",
    "geography": "climate, rivers, landforms, resources, agriculture, industries, cities",
    "environment": "ecology, biodiversity, climate change, conservation, pollution",
    "science_tech": "science, technology, space, biotechnology, computing, health tech",
}

SUBJECT_ITEMS: list[tuple[str, str]] = [
    ("Which Article of the Constitution empowers Parliament to make laws on a State List subject in the national interest?", "polity"),
    ("Examine the role of the Speaker in the disqualification of members under the anti-defection law.", "polity"),
    ("The doctrine of basic structure was propounded in which landmark case?", "polity"),
    ("Discuss the significance of the Finance Commission in Indian federalism.", "polity"),
    ("What is the difference between a Money Bill and a Financial Bill?", "polity"),
    ("Comment on the powers and functions of the Election Commission of India.", "polity"),
    ("How does the Monetary Policy Committee decide the repo rate to control inflation?", "economy"),
    ("Which of the following is included in the M3 measure of money supply?", "economy"),
    ("Examine the impact of Goods and Services Tax on India's federal fiscal structure.", "economy"),
    ("Discuss the factors responsible for the widening current account deficit.", "economy"),
    ("What is the difference between fiscal deficit and primary deficit?", "economy"),
    ("Evaluate the role of Self Help Groups in financial inclusion.", "economy"),
    ("Discuss the contribution of Ashoka's edicts to understanding Mauryan administration.", "history"),
    ("Which Viceroy introduced the Vernacular Press Act in 1878?", "history"),
    ("Examine the causes and consequences of the revolt of 1857.", "history"),
    ("Evaluate the role of the Gupta period in the development of Indian art and science.", "history"),
    ("The Dandi March was associated with the breaking of which law?", "history"),
    ("Comment on the significance of the Bhakti movement in medieval India.", "history"),
    ("Explain the formation of monsoon winds and the role of the Inter-Tropical Convergence Zone.", "geography"),
    ("Which river basin has the highest hydropower potential in India?", "geography"),
    ("Discuss the factors responsible for the location of the iron and steel industry in India.", "geography"),
    ("Examine the causes of urban flooding in Indian cities.", "geography"),
    ("What are the characteristics of the tropical deciduous forests?", "geography"),
    ("Account for the regional variation in the distribution of rainfall in India.", "geography"),
    ("What is the objective of the Convention on Biological Diversity?", "environment"),
    ("Discuss the role of mangrove ecosystems in coastal protection.", "environment"),
    ("Which gas is primarily responsible for the depletion of the ozone layer?", "environment"),
    ("Evaluate the effectiveness of the Environment Impact Assessment process in India.", "environment"),
    ("Examine the impact of climate change on Himalayan glaciers.", "environment"),
    ("What is the purpose of the Project Tiger initiative?", "environment"),
    ("What is the principle behind CRISPR gene editing technology?", "science_tech"),
    ("Discuss the applications of artificial intelligence in healthcare and associated ethical concerns.", "science_tech"),
    ("Which type of satellite orbit is used by geostationary communication satellites?", "science_tech"),
    ("Examine the significance of mRNA vaccines in disease prevention.", "science_tech"),
    ("What is the difference between nuclear fission and nuclear fusion?", "science_tech"),
    ("Comment on India's progress in quantum computing.", "science_tech"),
]

DIRECTIVES = {
    "discuss": "give a balanced account of the issue with several dimensions",
    "critically_examine": "examine closely and weigh strengths against weaknesses before judging",
    "comment": "give a reasoned opinion on the statement or idea",
    "analyse": "break the issue into parts and explain causes, links and implications",
    "evaluate": "judge the success, value or effectiveness using evidence",
    "examine": "inspect the topic in detail and explain its significance or causes",
    "elucidate": "make the concept clear with explanation and illustration",
    "account_for": "give reasons why something happened or exists",
    "explain": "describe how or why something works or happens",
    "compare": "set two or more things side by side showing similarities and differences",
}

DIRECTIVE_ITEMS: list[tuple[str, str]] = [
    ("Discuss the role of the judiciary in protecting fundamental rights.", "discuss"),
    ("Discuss the challenges of urbanisation in India.", "discuss"),
    ("Discuss the importance of cooperative federalism.", "discuss"),
    ("Critically examine the effectiveness of the anti-defection law.", "critically_examine"),
    ("Critically examine the impact of farm subsidies on groundwater.", "critically_examine"),
    ("Critically examine the role of NITI Aayog.", "critically_examine"),
    ("Comment on the idea of one nation one election.", "comment"),
    ("Comment on the role of microfinance in rural development.", "comment"),
    ("Comment on the relevance of Gandhian philosophy today.", "comment"),
    ("Analyse the causes of the agrarian crisis in India.", "analyse"),
    ("Analyse the factors behind the rise of regional parties.", "analyse"),
    ("Analyse the impact of globalisation on Indian culture.", "analyse"),
    ("Evaluate the success of the Green Revolution.", "evaluate"),
    ("Evaluate the role of the media in a democracy.", "evaluate"),
    ("Evaluate the impact of demonetisation on the informal economy.", "evaluate"),
    ("Examine the significance of the Preamble.", "examine"),
    ("Examine the causes of the decline of cottage industries.", "examine"),
    ("Examine the role of women in the freedom struggle.", "examine"),
    ("Elucidate the concept of constitutional morality.", "elucidate"),
    ("Elucidate the features of Indus Valley urban planning.", "elucidate"),
    ("Elucidate the meaning of sustainable development.", "elucidate"),
    ("Account for the delay in the completion of infrastructure projects in India.", "account_for"),
    ("Account for the uneven distribution of population in India.", "account_for"),
    ("Account for the declining sex ratio in some states.", "account_for"),
    ("Explain the mechanism of cyclone formation.", "explain"),
    ("Explain the concept of fiscal federalism.", "explain"),
    ("Explain how El Nino affects the Indian monsoon.", "explain"),
    ("Compare the Indian and American models of federalism.", "compare"),
    ("Compare the early and later Vedic societies.", "compare"),
    ("Compare the roles of the Lok Sabha and Rajya Sabha.", "compare"),
]


def build_question(qid: str, instructions: str, labels: dict[str, str]) -> dict:
    """Build a laya `choice` question; refuses label spaces above the model card's recommended size."""
    if len(labels) > MAX_OPTIONS:
        raise ValueError(f"{qid}: {len(labels)} options exceeds the recommended maximum of {MAX_OPTIONS}")
    return {"type": "choice", "instructions": instructions, "criteria": dict(labels)}
