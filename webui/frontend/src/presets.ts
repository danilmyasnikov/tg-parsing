export type Preset = {
  id: string
  label: string
  template: string
  hint: string
}

export const PRESETS: Preset[] = [
  {
    id: 'trend-summary',
    label: 'Summary of trends',
    hint: 'Scan channels for recurring topics and shifts.',
    template:
      'Write a concise trend summary based on the selected Telegram channels. Highlight 3-5 emerging themes and why they matter.',
  },
  {
    id: 'thought-provoking',
    label: 'Thought provoking post',
    hint: 'Open with a bold perspective or contrarian take.',
    template:
      'Create a thought-provoking post that challenges a common assumption found in the recent Telegram discussion. End with a question.',
  },
  {
    id: 'industry-brief',
    label: 'Industry brief',
    hint: 'Bullet points with a quick takeaway.',
    template:
      'Generate a short industry brief with 4 bullet points and a one-sentence takeaway at the end.',
  },
  {
    id: 'hooks',
    label: 'Hook + value',
    hint: 'Start with a hook, then deliver practical insight.',
    template:
      'Start with a hook in one sentence, then deliver practical value in 4-6 sentences. Keep the tone confident and clear.',
  },
  {
    id: 'debunk',
    label: 'Debunk a myth',
    hint: 'Address a misconception and replace it with truth.',
    template:
      'Debunk a common misconception reflected in the channels. Explain the reality with evidence-like reasoning and give a clear takeaway.',
  },
  {
    id: 'actionable-steps',
    label: 'Actionable steps',
    hint: 'List steps with a friendly, direct tone.',
    template:
      'Write a post that gives 5 actionable steps based on the conversation patterns. Keep each step short and practical.',
  },
]
