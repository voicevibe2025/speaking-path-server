from rest_framework import serializers


class ConversationTurnSerializer(serializers.Serializer):
    speaker = serializers.CharField()
    text = serializers.CharField()


class PhraseProgressSerializer(serializers.Serializer):
    currentPhraseIndex = serializers.IntegerField()
    completedPhrases = serializers.ListField(child=serializers.IntegerField())
    totalPhrases = serializers.IntegerField()
    isAllPhrasesCompleted = serializers.BooleanField()


class PracticeScoresSerializer(serializers.Serializer):
    pronunciation = serializers.IntegerField()
    fluency = serializers.IntegerField()
    vocabulary = serializers.IntegerField()
    listening = serializers.IntegerField(required=False)
    grammar = serializers.IntegerField(required=False)
    average = serializers.FloatField()
    meetsRequirement = serializers.BooleanField()
    # New fields for per-practice thresholds and combined progress bar
    maxPronunciation = serializers.IntegerField()
    maxFluency = serializers.IntegerField()
    maxVocabulary = serializers.IntegerField()
    maxListening = serializers.IntegerField(required=False)
    maxGrammar = serializers.IntegerField(required=False)
    pronunciationMet = serializers.BooleanField()
    fluencyMet = serializers.BooleanField()
    vocabularyMet = serializers.BooleanField()
    listeningMet = serializers.BooleanField(required=False)
    grammarMet = serializers.BooleanField(required=False)
    totalScore = serializers.IntegerField()
    totalMaxScore = serializers.IntegerField()
    combinedThresholdScore = serializers.IntegerField()
    combinedPercent = serializers.FloatField()
    thresholdPercent = serializers.IntegerField()


class SpeakingTopicDtoSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    material = serializers.ListField(child=serializers.CharField())
    vocabulary = serializers.ListField(child=serializers.CharField(), required=False)
    conversation = ConversationTurnSerializer(many=True, required=False)
    fluencyPracticePrompts = serializers.ListField(child=serializers.CharField(), required=False)
    fluencyProgress = serializers.DictField(child=serializers.JSONField(), required=False)
    phraseProgress = PhraseProgressSerializer(required=False)
    practiceScores = PracticeScoresSerializer(required=False)
    # Conversation practice progress (bonus mode)
    conversationScore = serializers.IntegerField(required=False)
    conversationCompleted = serializers.BooleanField(required=False)
    unlocked = serializers.BooleanField()
    completed = serializers.BooleanField()


class UserProfileSerializer(serializers.Serializer):
    firstVisit = serializers.BooleanField()
    lastVisitedTopicId = serializers.CharField(allow_null=True, required=False)
    lastVisitedTopicTitle = serializers.CharField(allow_blank=True, required=False)


class SpeakingTopicsResponseSerializer(serializers.Serializer):
    topics = SpeakingTopicDtoSerializer(many=True)
    userProfile = UserProfileSerializer()


class CompleteTopicResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    completedTopicId = serializers.CharField()
    unlockedTopicId = serializers.CharField(allow_null=True)


class PhraseSubmissionResultSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    accuracy = serializers.FloatField()
    transcription = serializers.CharField()
    feedback = serializers.CharField(allow_blank=True, required=False)
    nextPhraseIndex = serializers.IntegerField(allow_null=True, required=False)
    topicCompleted = serializers.BooleanField(default=False)
    xpAwarded = serializers.IntegerField(default=0)
    recordingId = serializers.CharField(allow_null=True, required=False)
    audioUrl = serializers.CharField(allow_blank=True, required=False)


class ConversationSubmissionResultSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    accuracy = serializers.FloatField()
    transcription = serializers.CharField()
    feedback = serializers.CharField(allow_blank=True, required=False)
    nextTurnIndex = serializers.IntegerField(allow_null=True, required=False)
    topicCompleted = serializers.BooleanField(default=False)
    xpAwarded = serializers.IntegerField(default=0)
    recordingId = serializers.CharField(allow_null=True, required=False)
    audioUrl = serializers.CharField(allow_blank=True, required=False)


class UserPhraseRecordingSerializer(serializers.Serializer):
    id = serializers.CharField()
    phraseIndex = serializers.IntegerField(source='phrase_index')
    audioUrl = serializers.SerializerMethodField()
    transcription = serializers.CharField(allow_blank=True)
    accuracy = serializers.FloatField(allow_null=True)
    feedback = serializers.CharField(allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at')

    def get_audioUrl(self, obj):
        request = self.context.get('request') if hasattr(self, 'context') else None
        try:
            url = obj.audio_file.url if obj.audio_file else ''
        except Exception:
            url = ''
        if request and url:
            return request.build_absolute_uri(url)
        return url


class UserPhraseRecordingsResponseSerializer(serializers.Serializer):
    recordings = UserPhraseRecordingSerializer(many=True)


class FluencyProgressSerializer(serializers.Serializer):
    promptsCount = serializers.IntegerField()
    promptScores = serializers.ListField(child=serializers.IntegerField())
    totalScore = serializers.IntegerField()
    nextPromptIndex = serializers.IntegerField(allow_null=True)
    completed = serializers.BooleanField()


class SubmitFluencyPromptRequestSerializer(serializers.Serializer):
    promptIndex = serializers.IntegerField()
    score = serializers.IntegerField(min_value=0)
    sessionId = serializers.CharField(allow_blank=True, required=False)


class SubmitFluencyPromptResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    nextPromptIndex = serializers.IntegerField(allow_null=True)
    fluencyTotalScore = serializers.IntegerField()
    fluencyCompleted = serializers.BooleanField()
    promptScores = serializers.ListField(child=serializers.IntegerField())
    xpAwarded = serializers.IntegerField(default=0)


# --- Vocabulary Practice ---
class VocabularyQuestionSerializer(serializers.Serializer):
    id = serializers.CharField()
    definition = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class StartVocabularyPracticeResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    totalQuestions = serializers.IntegerField()
    questions = VocabularyQuestionSerializer(many=True)


class SubmitVocabularyAnswerRequestSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    questionId = serializers.CharField()
    selected = serializers.CharField()


class SubmitVocabularyAnswerResponseSerializer(serializers.Serializer):
    correct = serializers.BooleanField()
    xpAwarded = serializers.IntegerField()
    nextIndex = serializers.IntegerField(allow_null=True)
    completed = serializers.BooleanField()
    totalScore = serializers.IntegerField()


class CompleteVocabularyPracticeRequestSerializer(serializers.Serializer):
    sessionId = serializers.CharField()


class CompleteVocabularyPracticeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalQuestions = serializers.IntegerField()
    correctCount = serializers.IntegerField()
    totalScore = serializers.IntegerField()
    xpAwarded = serializers.IntegerField()
    vocabularyTotalScore = serializers.IntegerField()
    topicCompleted = serializers.BooleanField()


# --- Listening Practice ---
class ListeningQuestionSerializer(serializers.Serializer):
    id = serializers.CharField()
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class StartListeningPracticeResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    totalQuestions = serializers.IntegerField()
    questions = ListeningQuestionSerializer(many=True)


class SubmitListeningAnswerRequestSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    questionId = serializers.CharField()
    selected = serializers.CharField()


class SubmitListeningAnswerResponseSerializer(serializers.Serializer):
    correct = serializers.BooleanField()
    xpAwarded = serializers.IntegerField()
    nextIndex = serializers.IntegerField(allow_null=True)
    completed = serializers.BooleanField()
    totalScore = serializers.IntegerField()


class CompleteListeningPracticeRequestSerializer(serializers.Serializer):
    sessionId = serializers.CharField()


class CompleteListeningPracticeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalQuestions = serializers.IntegerField()
    correctCount = serializers.IntegerField()
    totalScore = serializers.IntegerField()
    xpAwarded = serializers.IntegerField()
    listeningTotalScore = serializers.IntegerField()
    topicCompleted = serializers.BooleanField()


# --- Grammar Practice Serializers ---
class GrammarQuestionSerializer(serializers.Serializer):
    id = serializers.CharField()
    sentence = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())


class StartGrammarPracticeResponseSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    totalQuestions = serializers.IntegerField()
    questions = GrammarQuestionSerializer(many=True)


class SubmitGrammarAnswerRequestSerializer(serializers.Serializer):
    sessionId = serializers.CharField()
    questionId = serializers.CharField()
    selected = serializers.CharField()


class SubmitGrammarAnswerResponseSerializer(serializers.Serializer):
    correct = serializers.BooleanField()
    xpAwarded = serializers.IntegerField()
    nextIndex = serializers.IntegerField(allow_null=True)
    completed = serializers.BooleanField()
    totalScore = serializers.IntegerField()


class CompleteGrammarPracticeRequestSerializer(serializers.Serializer):
    sessionId = serializers.CharField()


class CompleteGrammarPracticeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalQuestions = serializers.IntegerField()
    correctCount = serializers.IntegerField()
    totalScore = serializers.IntegerField()
    xpAwarded = serializers.IntegerField()
    grammarTotalScore = serializers.IntegerField()
    topicCompleted = serializers.BooleanField()


class JourneyActivitySerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    timestamp = serializers.DateTimeField()
    xpEarned = serializers.IntegerField(required=False)


# --- AI Coach (Gemini-as-GRU) ---
class CoachSkillSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    mastery = serializers.IntegerField(min_value=0, max_value=100)
    confidence = serializers.FloatField(required=False)
    trend = serializers.ChoiceField(choices=["up", "down", "flat"], required=False)
    evidence = serializers.ListField(child=serializers.CharField(), required=False)


class NextBestActionSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    rationale = serializers.CharField()
    deeplink = serializers.CharField()
    expectedGain = serializers.ChoiceField(choices=["small", "medium", "large"], required=False)


class DifficultyCalibrationSerializer(serializers.Serializer):
    pronunciation = serializers.ChoiceField(choices=["easier", "baseline", "harder"], required=False)
    fluency = serializers.ChoiceField(choices=["slower", "baseline", "faster"], required=False)
    vocabulary = serializers.ChoiceField(choices=["fewer_terms", "baseline", "more_terms"], required=False)


class CoachScheduleItemSerializer(serializers.Serializer):
    date = serializers.DateField()
    focus = serializers.CharField()
    microSkills = serializers.ListField(child=serializers.CharField(), required=False)
    reason = serializers.CharField(required=False)


class CoachAnalysisSerializer(serializers.Serializer):
    currentVersion = serializers.IntegerField()
    generatedAt = serializers.DateTimeField()
    skills = CoachSkillSerializer(many=True)
    strengths = serializers.ListField(child=serializers.CharField())
    weaknesses = serializers.ListField(child=serializers.CharField())
    nextBestActions = NextBestActionSerializer(many=True)
    difficultyCalibration = DifficultyCalibrationSerializer(required=False)
    schedule = CoachScheduleItemSerializer(many=True, required=False)
    coachMessage = serializers.CharField()
    cacheForHours = serializers.IntegerField(default=12)
