"""Landing starter prompts API."""

import re

from api.rag.starter_prompts import StarterPromptKind, build_starter_prompts


def test_starter_prompts_has_two_corpus_and_one_off_topic():
    prompts = build_starter_prompts()
    assert len(prompts) == 3
    kinds = [p.kind for p in prompts]
    assert kinds.count(StarterPromptKind.CORPUS) == 2
    assert kinds.count(StarterPromptKind.OFF_TOPIC) == 1
    assert prompts[-1].kind == StarterPromptKind.OFF_TOPIC


def test_second_prompt_is_a_date_list_query():
    prompts = build_starter_prompts()
    middle = prompts[1]
    assert middle.kind == StarterPromptKind.CORPUS
    # Carries an ISO date and asks for "all research" on that date.
    assert re.search(r"\d{4}-\d{2}-\d{2}", middle.query)
    assert "research" in middle.query.lower()


def test_first_prompt_is_corpus_latest_article():
    prompts = build_starter_prompts()
    assert prompts[0].kind == StarterPromptKind.CORPUS

