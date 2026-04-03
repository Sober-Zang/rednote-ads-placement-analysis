.PHONY: build verify-skill skill-enable skill-disable skill-status

build:
	@./scripts/build_with_skill.sh "$(CMD)"

verify-skill:
	@python3 ./scripts/validate_skill_creator_env.py --project-root .

skill-enable:
	@./scripts/skill_state.sh enable

skill-disable:
	@./scripts/skill_state.sh disable

skill-status:
	@./scripts/skill_state.sh status
