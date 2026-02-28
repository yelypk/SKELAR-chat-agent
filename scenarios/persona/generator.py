from __future__ import annotations

import random

from engine.state import PersonaSeed, SupportPersonaSeed


GENDERS = ["Male", "Female", "Non-binary"]
GENERATIONS = ["boomer", "millennial", "gen_z"]
SOCIAL_STATUS = ["low_income", "middle_class", "affluent"]
EDUCATION_LEVELS = ["secondary", "bachelor", "master", "self_taught"]
MBTI_TYPES = [
    "INTJ",
    "INTP",
    "ENTJ",
    "ENTP",
    "INFJ",
    "INFP",
    "ENFJ",
    "ENFP",
    "ISTJ",
    "ISFJ",
    "ESTJ",
    "ESFJ",
    "ISTP",
    "ISFP",
    "ESTP",
    "ESFP",
]
EMOTIONAL_STATES = ["anxious", "irritated", "calm", "suspicious", "fatigued"]
LEVELS = ["low", "medium", "high"]
SUPPORT_SENIORITY = ["junior", "middle", "senior", "lead"]
SUPPORT_COMMUNICATION_STYLES = ["formal", "friendly", "concise", "empathetic"]


def _level_weight(value: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}[value]


def generate_persona_seed(rng: random.Random) -> tuple[PersonaSeed, dict]:
    gender = rng.choice(GENDERS)
    generation = rng.choice(GENERATIONS)
    social_status = rng.choice(SOCIAL_STATUS)
    education = rng.choice(EDUCATION_LEVELS)
    mbti_seed = rng.choice(MBTI_TYPES)
    impulsiveness = rng.choice(LEVELS)
    volatility_trust = rng.choice(LEVELS)
    communication_noise = rng.choice(LEVELS)
    emotional_state = rng.choice(EMOTIONAL_STATES)
    intensity = (
        _level_weight(impulsiveness)
        + _level_weight(volatility_trust)
        + _level_weight(communication_noise)
    )
    if intensity <= 4:
        chaos_level = "low"
    elif intensity <= 7:
        chaos_level = "medium"
    else:
        chaos_level = "high"

    persona = PersonaSeed(
        gender=gender,
        generation=generation,
        social_status=social_status,
        education=education,
        mbti_seed=mbti_seed,
        emotional_state=emotional_state,
        impulsiveness=impulsiveness,
        volatility_trust=volatility_trust,
        communication_noise=communication_noise,
        chaos_level=chaos_level,
        persona_seed_prompt=(
            "A customer with unstable emotional regulation, variable trust, and noisy "
            "communication style. Keep behavior high-variance but logically consistent with "
            "known facts.\n"
            f"Gender: {gender}. Generation: {generation}. "
            f"Social status: {social_status}. Education: {education}. "
            f"MBTI seed: {mbti_seed}. Emotional state: {emotional_state}. "
            f"Impulsiveness: {impulsiveness}. Trust volatility: {volatility_trust}. "
            f"Communication noise: {communication_noise}."
        ),
    )
    entropy_params = {
        "impulsiveness": impulsiveness,
        "volatility_trust": volatility_trust,
        "communication_noise": communication_noise,
        "chaos_level": chaos_level,
    }
    return persona, entropy_params


def generate_support_persona_seed(rng: random.Random) -> SupportPersonaSeed:
    gender = rng.choice(GENDERS)
    generation = rng.choice(GENERATIONS)
    education = rng.choice(EDUCATION_LEVELS)
    communication_style = rng.choice(SUPPORT_COMMUNICATION_STYLES)
    seniority = rng.choice(SUPPORT_SENIORITY)
    return SupportPersonaSeed(
        gender=gender,
        generation=generation,
        education=education,
        communication_style=communication_style,
        seniority=seniority,
        support_persona_seed_prompt=(
            "A technical support agent with workplace communication standards. "
            f"Gender: {gender}. Generation: {generation}. Education: {education}. "
            f"Communication style: {communication_style}. Seniority: {seniority}. "
            "Follow professional support workflow while staying natural and helpful."
        ),
    )
