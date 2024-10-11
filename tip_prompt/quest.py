from typing import List, Dict, Optional

__all__ = ['QuestTypes', 'QuestionOption', 'QuestRef', 'QuestStem', 'KnowledgePoint', 'Question']


class QuestTypes:
    CHOICE = 'CHOICE'
    BLANK = 'BLANK'
    JUDGE = 'JUDGE'
    COMPLEX = 'COMPLEX'
    OTHER = 'OTHER'
    NORMAL = 'NORMAL'


class QuestionOption:
    def __init__(self, bullet: Optional[str] = None, text: Optional[str] = None):
        if bullet:
            bullet = bullet.strip()
        self.bullet = bullet
        if text:
            text = text.strip()
        self.text = text

    @staticmethod
    def from_str(text: str):
        bullets = ['A.', 'B.', 'C.', 'D.']
        for bullet in bullets:
            if text.startswith(bullet):
                return QuestionOption(bullet=bullet, text=text[2:])
        return QuestionOption(bullet=None, text=text)

    @staticmethod
    def from_json(jd: Dict):
        return QuestionOption(bullet=jd.get('bullet'), text=jd.get('text'))

    def to_json(self):
        return {
            'bullet': self.bullet,
            'text': self.text
        }


class QuestRef:

    def __init__(self, texts: List[str], analyses: List[str] = None):
        self.texts = texts or []
        self.analyses = analyses or []

    @staticmethod
    def from_json(jd: Dict):
        return QuestRef(texts=jd.get('texts'), analyses=jd.get('analyses'))

    def to_json(self):
        ret = {}
        if self.texts:
            ret['texts'] = self.texts
        if self.analyses:
            ret['analyses'] = self.analyses
        return ret


class QuestStem:
    """题干"""

    def __init__(self, text: str, options: List[QuestionOption] = None):
        self.text = text or ''
        self.options = options or []

    def get_stem(self):
        options = " ".join(o.bullet + '.' + o.text for o in self.options)
        return self.text + '\n' + options

    @staticmethod
    def from_json(jd: Dict):
        return QuestStem(text=jd.get('text', ''),
                         options=[QuestionOption.from_json(jd_option) for jd_option in jd.get('options', [])])

    def to_json(self):
        ret = {'text': self.text}
        if self.options:
            ret['options'] = [option.to_json() for option in self.options]
        return ret


class KnowledgePoint:
    """知识点"""

    def __init__(self, text: str, grade: int):
        self.text = text
        self.grade = grade

    @staticmethod
    def from_json(jd: Dict):
        return KnowledgePoint(text=jd.get('text', ''), grade=jd.get('grade', ''))

    def to_json(self):
        ret = {
            'text': self.text,
            'grade': self.grade
        }
        return ret


class Question:

    def __init__(self, quest_stem: QuestStem, quest_id: str = None, quest_ref: QuestRef = None,
                 sub_quests: List['Question'] = None, qtype=None, knowledge_points: List[KnowledgePoint] = None,
                 similar_quests: List['Question'] = None, generate_ref: QuestRef = None,
                 related_st_questions: List[str] = None, unrelated_st_questions: List[str] = None):
        self.qtype = qtype
        self.quest_stem = quest_stem
        self.quest_ref = quest_ref
        self.quest_id = quest_id
        self.sub_quests = sub_quests or []
        self.knowledge_points = knowledge_points or []
        self.similar_quests = similar_quests or []
        self.generate_ref = generate_ref
        self.related_st_questions = related_st_questions or []
        self.unrelated_st_questions = unrelated_st_questions or []

    @staticmethod
    def from_json(jd: Dict):
        sub_quests = []
        knowledge_points = []
        similar_quests = []
        if 'sub_quests' in jd:
            sub_quests = [Question.from_json(sub_quest) for sub_quest in jd['sub_quests']]
        if 'knowledge_points' in jd:
            knowledge_points = [KnowledgePoint.from_json(knowledge_point) for knowledge_point in jd['knowledge_points']]
        if 'similar_quests' in jd:
            similar_quests = [Question.from_json(similar_quest) for similar_quest in jd['similar_quests']]
        return Question(qtype=jd.get('qtype'), quest_id=jd.get('quest_id', None),
                        quest_stem=QuestStem.from_json(jd.get('quest_stem', {})),
                        quest_ref=QuestRef.from_json(jd.get('quest_ref', {})), sub_quests=sub_quests,
                        knowledge_points=knowledge_points, similar_quests=similar_quests,
                        related_st_questions=jd.get('related_st_questions', None),
                        unrelated_st_questions=jd.get('unrelated_st_questions', None)
                        )

    def to_json(self):
        ret = {'qtype': self.qtype}
        if self.quest_stem:
            ret['quest_stem'] = self.quest_stem.to_json()
        if self.quest_ref:
            ret['quest_ref'] = self.quest_ref.to_json()
        if self.sub_quests:
            ret['sub_quests'] = [sub_quest.to_json() for sub_quest in self.sub_quests]
        if self.knowledge_points:
            ret['knowledge_points'] = [knowledge_point.to_json() for knowledge_point in self.knowledge_points]
        if self.similar_quests:
            ret['similar_quests'] = [similar_quest.to_json() for similar_quest in self.similar_quests]
        ret['related_st_questions'] = self.related_st_questions
        ret['unrelated_st_questions'] = self.unrelated_st_questions
        return ret

    def _get_analyses(self):
        if self.quest_ref:
            return self.quest_ref.analyses
        return []

    def _get_all_analyses(self) -> List[str]:
        analyses = self._get_analyses()
        for sub_quest in self.sub_quests:
            analyses.extend(sub_quest._get_analyses())
        return analyses

    def has_analysis(self):
        return len(self._get_all_analyses()) > 0
