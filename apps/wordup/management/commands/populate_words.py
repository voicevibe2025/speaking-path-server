from django.core.management.base import BaseCommand
from apps.wordup.models import Word


class Command(BaseCommand):
    help = 'Populate initial vocabulary words for WordUp feature'

    def handle(self, *args, **options):
        words_data = [
            # Beginner words
            {
                'word': 'abandon',
                'definition': 'To leave behind or give up completely',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'They had to abandon their car in the storm.',
                'ipa_pronunciation': '/əˈbændən/'
            },
            {
                'word': 'brave',
                'definition': 'Showing courage and fearlessness',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was brave enough to speak in front of the crowd.',
                'ipa_pronunciation': '/breɪv/'
            },
            {
                'word': 'curious',
                'definition': 'Eager to learn or know something',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'Children are naturally curious about the world.',
                'ipa_pronunciation': '/ˈkjʊəriəs/'
            },
            {
                'word': 'delicious',
                'definition': 'Having a very pleasant taste',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The cake was absolutely delicious.',
                'ipa_pronunciation': '/dɪˈlɪʃəs/'
            },
            {
                'word': 'enormous',
                'definition': 'Very large in size or quantity',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The elephant was enormous compared to the dog.',
                'ipa_pronunciation': '/ɪˈnɔːrməs/'
            },
            {
                'word': 'frequent',
                'definition': 'Happening often or at short intervals',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'He is a frequent visitor to the library.',
                'ipa_pronunciation': '/ˈfriːkwənt/'
            },
            {
                'word': 'gentle',
                'definition': 'Having a mild, kind, or tender temperament or character',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The dog was very gentle with the children.',
                'ipa_pronunciation': '/ˈdʒentl/'
            },
            {
                'word': 'happy',
                'definition': 'Feeling or showing pleasure or contentment',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was happy to see her friends again.',
                'ipa_pronunciation': '/ˈhæpi/'
            },
            {
                'word': 'imagine',
                'definition': 'To form a mental image or concept of',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'Can you imagine a world without music?',
                'ipa_pronunciation': '/ɪˈmædʒɪn/'
            },
            {
                'word': 'journey',
                'definition': 'An act of traveling from one place to another',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'The journey to the mountains was long but beautiful.',
                'ipa_pronunciation': '/ˈdʒɜːrni/'
            },
            {
                'word': 'kind',
                'definition': 'Having a friendly, generous, and considerate nature.',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'It was very kind of you to help me.',
                'ipa_pronunciation': '/kaɪnd/'
            },
            {
                'word': 'laugh',
                'definition': 'Make the spontaneous sounds and movements of the face and body that are the instinctive expressions of lively amusement and sometimes also of derision.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'She started to laugh uncontrollably.',
                'ipa_pronunciation': '/læf/'
            },
            {
                'word': 'music',
                'definition': 'Vocal or instrumental sounds (or both) combined in such a way as to produce beauty of form, harmony, and expression of emotion.',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'The music was playing softly in the background.',
                'ipa_pronunciation': '/ˈmjuːzɪk/'
            },
            {
                'word': 'ocean',
                'definition': 'A very large expanse of sea, in particular each of the main areas into which the sea is divided geographically.',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'The ocean waves crashed against the shore.',
                'ipa_pronunciation': '/ˈoʊʃn/'
            },
            {
                'word': 'quiet',
                'definition': 'Making little or no noise.',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The library was a quiet place to study.',
                'ipa_pronunciation': '/ˈkwaɪət/'
            },
            {
                'word': 'read',
                'definition': 'To look at and comprehend the meaning of written or printed matter.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'I like to read a book before I go to sleep.',
                'ipa_pronunciation': '/riːd/'
            },
            {
                'word': 'sing',
                'definition': 'To make musical sounds with the voice.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'She loves to sing in the shower.',
                'ipa_pronunciation': '/sɪŋ/'
            },
            {
                'word': 'talk',
                'definition': 'To speak in order to give information or express ideas or feelings.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'We need to talk about our plans for the weekend.',
                'ipa_pronunciation': '/tɔːk/'
            },
            {
                'word': 'use',
                'definition': 'To take, hold, or deploy as a means of accomplishing a purpose.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'Can I use your pen for a moment?',
                'ipa_pronunciation': '/juːz/'
            },
            {
                'word': 'walk',
                'definition': 'To move at a regular pace by lifting and setting down each foot in turn, never having both feet off the ground at once.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'I walk to work every day.',
                'ipa_pronunciation': '/wɔːk/'
            },
            {
                'word': 'work',
                'definition': 'Activity involving mental or physical effort done in order to achieve a purpose or result.',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'He has a lot of work to do.',
                'ipa_pronunciation': '/wɜːrk/'
            },
            {
                'word': 'write',
                'definition': 'To mark on a surface, typically paper, with a pen, pencil, or similar implement.',
                'difficulty': 'beginner',
                'part_of_speech': 'verb',
                'example_sentence': 'She is learning to write her name.',
                'ipa_pronunciation': '/raɪt/'
            },
            {
                'word': 'young',
                'definition': 'Having lived or existed for only a short time.',
                'difficulty': 'beginner',
                'part_of_speech': 'adjective',
                'example_sentence': 'The young cat was very playful.',
                'ipa_pronunciation': '/jʌŋ/'
            },
            {
                'word': 'zone',
                'definition': 'An area or stretch of land having a particular characteristic, purpose, or use, or subject to particular restrictions.',
                'difficulty': 'beginner',
                'part_of_speech': 'noun',
                'example_sentence': 'This is a pedestrian-only zone.',
                'ipa_pronunciation': '/zoʊn/'
            },
            # Intermediate words
            {
                'word': 'ambiguous',
                'definition': 'Open to more than one interpretation; not clear',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'His answer was ambiguous and left us confused.',
                'ipa_pronunciation': '/æmˈbɪɡjuəs/'
            },
            {
                'word': 'benevolent',
                'definition': 'Well-meaning and kindly',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was known for her benevolent nature and generous donations.',
                'ipa_pronunciation': '/bəˈnevələnt/'
            },
            {
                'word': 'comprehend',
                'definition': 'To understand fully',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'It took me a while to comprehend the complex theory.',
                'ipa_pronunciation': '/ˌkɑːmprɪˈhend/'
            },
            {
                'word': 'diligent',
                'definition': 'Showing care and effort in work or duties',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a diligent student who always completed his homework.',
                'ipa_pronunciation': '/ˈdɪlɪdʒənt/'
            },
            {
                'word': 'eloquent',
                'definition': 'Fluent and persuasive in speaking or writing',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The speaker gave an eloquent presentation that moved the audience.',
                'ipa_pronunciation': '/ˈeləkwənt/'
            },
            {
                'word': 'facilitate',
                'definition': 'To make an action or process easy or easier',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'The new software will facilitate data analysis.',
                'ipa_pronunciation': '/fəˈsɪlɪteɪt/'
            },
            {
                'word': 'harmonious',
                'definition': 'Forming a pleasing or consistent whole',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'They lived in a harmonious relationship with their neighbors.',
                'ipa_pronunciation': '/hɑːrˈmoʊniəs/'
            },
            {
                'word': 'illustrate',
                'definition': 'To explain or make clear by using examples, charts, or pictures',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'The teacher used diagrams to illustrate the concept.',
                'ipa_pronunciation': '/ˈɪləstreɪt/'
            },
            {
                'word': 'meticulous',
                'definition': 'Showing great attention to detail; very careful and precise',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was meticulous in his preparation for the presentation.',
                'ipa_pronunciation': '/məˈtɪkjələs/'
            },
            {
                'word': 'navigate',
                'definition': 'To plan and direct the route or course of a ship, aircraft, or other form of transport, especially by using instruments or maps',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'It was difficult to navigate through the dense fog.',
                'ipa_pronunciation': '/ˈnævɪɡeɪt/'
            },
            {
                'word': 'nostalgia',
                'definition': 'A sentimental longing or wistful affection for the past, typically for a period or place with happy personal associations.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'He was filled with nostalgia for his college days.',
                'ipa_pronunciation': '/nəˈstældʒə/'
            },
            {
                'word': 'obsolete',
                'definition': 'No longer produced or used; out of date.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The typewriter has become obsolete with the advent of computers.',
                'ipa_pronunciation': '/ˌɑːbsəˈliːt/'
            },
            {
                'word': 'pragmatic',
                'definition': 'Dealing with things sensibly and realistically in a way that is based on practical rather than theoretical considerations.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She took a pragmatic approach to solving the problem.',
                'ipa_pronunciation': '/præɡˈmætɪk/'
            },
            {
                'word': 'resilient',
                'definition': 'Able to withstand or recover quickly from difficult conditions.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'Children are often more resilient than adults.',
                'ipa_pronunciation': '/rɪˈzɪliənt/'
            },
            {
                'word': 'skeptical',
                'definition': 'Not easily convinced; having doubts or reservations.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was skeptical about the claims made in the advertisement.',
                'ipa_pronunciation': '/ˈskeptɪkl/'
            },
            {
                'word': 'tenacious',
                'definition': 'Tending to keep a firm hold of something; clinging or adhering closely.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was tenacious in her pursuit of her goals.',
                'ipa_pronunciation': '/təˈneɪʃəs/'
            },
            {
                'word': 'ubiquitous',
                'definition': 'Present, appearing, or found everywhere.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'Mobile phones are now ubiquitous around the world.',
                'ipa_pronunciation': '/juːˈbɪkwɪtəs/'
            },
            {
                'word': 'validate',
                'definition': 'To check or prove the validity or accuracy of something.',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'You need to validate your email address to complete the registration.',
                'ipa_pronunciation': '/ˈvælɪdeɪt/'
            },
            {
                'word': 'whimsical',
                'definition': 'Playfully quaint or fanciful, especially in an appealing and amusing way.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The whimsical decorations made the room feel magical.',
                'ipa_pronunciation': '/ˈwɪmzɪkl/'
            },
            {
                'word': 'yearn',
                'definition': 'To have an intense feeling of longing for something, typically something that one has lost or been separated from.',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'She yearned for the simple days of her childhood.',
                'ipa_pronunciation': '/jɜːrn/'
            },
            {
                'word': 'zealous',
                'definition': 'Having or showing zeal.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a zealous supporter of the new policy.',
                'ipa_pronunciation': '/ˈzeləs/'
            },
            {
                'word': 'acquiesce',
                'definition': 'To accept something reluctantly but without protest.',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'She acquiesced to their demands.',
                'ipa_pronunciation': '/ˌækwiˈes/'
            },
            {
                'word': 'belligerent',
                'definition': 'Hostile and aggressive.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The belligerent man was shouting at the waiter.',
                'ipa_pronunciation': '/bəˈlɪdʒərənt/'
            },
            {
                'word': 'capitulate',
                'definition': 'To cease to resist an opponent or an unwelcome demand; surrender.',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'The army was forced to capitulate.',
                'ipa_pronunciation': '/kəˈpɪtʃəleɪt/'
            },
            {
                'word': 'fallacy',
                'definition': 'A mistaken belief, especially one based on unsound argument.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'The idea that money buys happiness is a fallacy.',
                'ipa_pronunciation': '/ˈfæləsi/'
            },
            {
                'word': 'facetious',
                'definition': 'Treating serious issues with deliberately inappropriate humor; flippant.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He made a facetious remark that was not appreciated.',
                'ipa_pronunciation': '/fəˈsiːʃəs/'
            },
            {
                'word': 'gregarious',
                'definition': 'Fond of company; sociable.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a gregarious and outgoing person.',
                'ipa_pronunciation': '/ɡrɪˈɡeəriəs/'
            },
            {
                'word': 'harangue',
                'definition': 'A lengthy and aggressive speech.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'He delivered a long harangue about the evils of modern society.',
                'ipa_pronunciation': '/həˈræŋ/'
            },
            {
                'word': 'iconoclast',
                'definition': 'A person who attacks cherished beliefs or institutions.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'The artist was an iconoclast who challenged traditional forms of art.',
                'ipa_pronunciation': '/aɪˈkɒnəklæst/'
            },
            {
                'word': 'juxtaposition',
                'definition': 'The fact of two things being seen or placed close together with contrasting effect.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'The juxtaposition of the old and new buildings was striking.',
                'ipa_pronunciation': '/ˌdʒʌkstəpəˈzɪʃn/'
            },
            {
                'word': 'kudos',
                'definition': 'Praise and honor received for an achievement.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'She received kudos for her hard work.',
                'ipa_pronunciation': '/ˈkjuːdɒs/'
            },
            {
                'word': 'laconic',
                'definition': 'Using very few words.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'His laconic reply suggested a lack of interest in the topic.',
                'ipa_pronunciation': '/ləˈkɒnɪk/'
            },
            {
                'word': 'magnanimous',
                'definition': 'Generous or forgiving, especially toward a rival or less powerful person.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The team was magnanimous in victory.',
                'ipa_pronunciation': '/mæɡˈnænɪməs/'
            },
            {
                'word': 'nefarious',
                'definition': 'Wicked or criminal.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The nefarious villain plotted to take over the world.',
                'ipa_pronunciation': '/nɪˈfeəriəs/'
            },
            {
                'word': 'obfuscate',
                'definition': 'To make something unclear or difficult to understand.',
                'difficulty': 'intermediate',
                'part_of_speech': 'verb',
                'example_sentence': 'The politician tried to obfuscate the issue.',
                'ipa_pronunciation': '/ˈɒbfʌskeɪt/'
            },
            {
                'word': 'pensive',
                'definition': 'Engaged in, involving, or reflecting deep or serious thought.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was in a pensive mood, staring out the window.',
                'ipa_pronunciation': '/ˈpensɪv/'
            },
            {
                'word': 'querulous',
                'definition': 'Complaining in a petulant or whining manner.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The querulous child was never satisfied.',
                'ipa_pronunciation': '/ˈkwerʊləs/'
            },
            {
                'word': 'recalcitrant',
                'definition': 'Having an obstinately uncooperative attitude toward authority or discipline.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The recalcitrant student refused to do his homework.',
                'ipa_pronunciation': '/rɪˈkælsɪtrənt/'
            },
            {
                'word': 'soporific',
                'definition': 'Tending to induce drowsiness or sleep.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The soporific effect of the drug was immediate.',
                'ipa_pronunciation': '/ˌsɒpəˈrɪfɪk/'
            },
            {
                'word': 'trepidation',
                'definition': 'A feeling of fear or agitation about something that may happen.',
                'difficulty': 'intermediate',
                'part_of_speech': 'noun',
                'example_sentence': 'He felt a sense of trepidation before the big exam.',
                'ipa_pronunciation': '/ˌtrepɪˈdeɪʃn/'
            },
            {
                'word': 'venerable',
                'definition': 'Accorded a great deal of respect, especially because of age, wisdom, or character.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'The venerable professor was a leading expert in his field.',
                'ipa_pronunciation': '/ˈvenərəbl/'
            },
            {
                'word': 'wistful',
                'definition': 'Having or showing a feeling of vague or regretful longing.',
                'difficulty': 'intermediate',
                'part_of_speech': 'adjective',
                'example_sentence': 'She had a wistful look on her face as she remembered her childhood.',
                'ipa_pronunciation': '/ˈwɪstfəl/'
            },
            # Advanced words
            {
                'word': 'aberration',
                'definition': 'A departure from what is normal or expected',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The warm weather in December was an aberration.',
                'ipa_pronunciation': '/ˌæbəˈreɪʃn/'
            },
            {
                'word': 'gregarious',
                'definition': 'Fond of company; sociable',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was gregarious and loved attending social events.',
                'ipa_pronunciation': '/ɡrɪˈɡeriəs/'
            },
            {
                'word': 'ephemeral',
                'definition': 'Lasting for a very short time',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The beauty of cherry blossoms is ephemeral, lasting only a week.',
                'ipa_pronunciation': '/ɪˈfemərəl/'
            },
            {
                'word': 'ubiquitous',
                'definition': 'Present, appearing, or found everywhere',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'Smartphones have become ubiquitous in modern society.',
                'ipa_pronunciation': '/juːˈbɪkwɪtəs/'
            },
            {
                'word': 'quintessential',
                'definition': 'Representing the most perfect example of something',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She is the quintessential professional, always punctual and prepared.',
                'ipa_pronunciation': '/ˌkwɪntɪˈsenʃl/'
            },
            {
                'word': 'cacophony',
                'definition': 'A harsh, discordant mixture of sounds',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'A cacophony of car horns filled the street during rush hour.',
                'ipa_pronunciation': '/kəˈkɑːfəni/'
            },
            {
                'word': 'deleterious',
                'definition': 'Causing harm or damage',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'Smoking has many deleterious effects on health.',
                'ipa_pronunciation': '/ˌdeləˈtɪriəs/'
            },
            {
                'word': 'esoteric',
                'definition': 'Intended for or likely to be understood by only a small number of people with a specialized knowledge or interest',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The book was full of esoteric references that only a few scholars could understand.',
                'ipa_pronunciation': '/ˌesəˈterɪk/'
            },
            {
                'word': 'paradigm',
                'definition': 'A typical example or pattern of something; a model',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The new discovery shifted the scientific paradigm.',
                'ipa_pronunciation': '/ˈpærədaɪm/'
            },
            {
                'word': 'serendipity',
                'definition': 'The occurrence and development of events by chance in a happy or beneficial way',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'Meeting her was pure serendipity; it changed my life for the better.',
                'ipa_pronunciation': '/ˌserənˈdɪpəti/'
            },
            {
                'word': 'sycophant',
                'definition': 'A person who acts obsequiously toward someone important in order to gain advantage.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The king was surrounded by sycophants who praised his every decision.',
                'ipa_pronunciation': '/ˈsɪkəfænt/'
            },
            {
                'word': 'taciturn',
                'definition': 'Reserved or uncommunicative in speech; saying little.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a taciturn man who rarely spoke about his feelings.',
                'ipa_pronunciation': '/ˈtæsɪtɜːrn/'
            },
            {
                'word': 'unctuous',
                'definition': 'Excessively flattering or ingratiating; oily.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'His unctuous praise made her feel uncomfortable.',
                'ipa_pronunciation': '/ˈʌŋktʃuəs/'
            },
            {
                'word': 'veracity',
                'definition': 'Conformity to facts; accuracy.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The veracity of his story was questionable.',
                'ipa_pronunciation': '/vəˈræsəti/'
            },
            {
                'word': 'zenith',
                'definition': 'The time at which something is most powerful or successful.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The Roman Empire reached its zenith in the 2nd century AD.',
                'ipa_pronunciation': '/ˈziːnɪθ/'
            },
            {
                'word': 'alacrity',
                'definition': 'Bris_of_speecha and cheerful readiness.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'She accepted the invitation with alacrity.',
                'ipa_pronunciation': '/əˈlækrəti/'
            },
            {
                'word': 'bombastic',
                'definition': 'High-sounding but with little meaning; inflated.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The politician\'s bombastic speech was full of empty promises.',
                'ipa_pronunciation': '/bɑːmˈbæstɪk/'
            },
            {
                'word': 'cognizant',
                'definition': 'Having knowledge or being aware of.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was cognizant of the risks involved.',
                'ipa_pronunciation': '/ˈkɑːɡnɪzənt/'
            },
            {
                'word': 'diatribe',
                'definition': 'A forceful and bitter verbal attack against someone or something.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The senator launched into a diatribe against the new tax bill.',
                'ipa_pronunciation': '/ˈdaɪətraɪb/'
            },
            {
                'word': 'ebullient',
                'definition': 'Cheerful and full of energy.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was in an ebullient mood after her victory.',
                'ipa_pronunciation': '/ɪˈbʌliənt/'
            },
            {
                'word': 'fastidious',
                'definition': 'Very attentive to and concerned about accuracy and detail.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'He was a fastidious dresser, always impeccably turned out.',
                'ipa_pronunciation': '/fæˈstɪdiəs/'
            },
            {
                'word': 'garrulous',
                'definition': 'Excessively talkative, especially on trivial matters.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The garrulous old man bored everyone with his stories.',
                'ipa_pronunciation': '/ˈɡærələs/'
            },
            {
                'word': 'hapless',
                'definition': 'Unfortunate.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The hapless victims of the earthquake were left homeless.',
                'ipa_pronunciation': '/ˈhæpləs/'
            },
            {
                'word': 'iconoclast',
                'definition': 'A person who attacks cherished beliefs or institutions.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The artist was an iconoclast who challenged traditional notions of beauty.',
                'ipa_pronunciation': '/aɪˈkɑːnəklæst/'
            },
            {
                'word': 'maverick',
                'definition': 'An unorthodox or independent-minded person.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'He was a maverick who refused to follow the rules.',
                'ipa_pronunciation': '/ˈmævərɪk/'
            },
            {
                'word': 'obfuscate',
                'definition': 'To render obscure, unclear, or unintelligible.',
                'difficulty': 'advanced',
                'part_of_speech': 'verb',
                'example_sentence': 'The politician tried to obfuscate the issue.',
                'ipa_pronunciation': '/ˈɒbfʌskeɪt/'
            },
            {
                'word': 'palliative',
                'definition': 'Relieving pain or alleviating a problem without dealing with the underlying cause.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The medicine was only a palliative, not a cure.',
                'ipa_pronunciation': '/ˈpæliətɪv/'
            },
            {
                'word': 'quixotic',
                'definition': 'Exceedingly idealistic; unrealistic and impractical.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'He had a quixotic dream of world peace.',
                'ipa_pronunciation': '/kwɪkˈsɒtɪk/'
            },
            {
                'word': 'rancorous',
                'definition': 'Characterized by bitterness or resentment.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The debate was rancorous and full of personal attacks.',
                'ipa_pronunciation': '/ˈræŋkərəs/'
            },
            {
                'word': 'sanguine',
                'definition': 'Optimistic or positive, especially in an apparently bad or difficult situation.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She was sanguine about the future.',
                'ipa_pronunciation': '/ˈsæŋɡwɪn/'
            },
            {
                'word': 'truculent',
                'definition': 'Eager or quick to argue or fight; aggressively defiant.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The truculent child refused to listen to his parents.',
                'ipa_pronunciation': '/ˈtrʌkjələnt/'
            },
            {
                'word': 'umbrage',
                'definition': 'Offense or annoyance.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'She took umbrage at his rude comment.',
                'ipa_pronunciation': '/ˈʌmbrɪdʒ/'
            },
            {
                'word': 'vituperative',
                'definition': 'Bitter and abusive.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'The vituperative review of the book was unfair.',
                'ipa_pronunciation': '/vɪˈtjuːpərətɪv/'
            },
            {
                'word': 'winsome',
                'definition': 'Attractive or appealing in appearance or character.',
                'difficulty': 'advanced',
                'part_of_speech': 'adjective',
                'example_sentence': 'She had a winsome smile that charmed everyone.',
                'ipa_pronunciation': '/ˈwɪnsəm/'
            },
            {
                'word': 'xenophobia',
                'definition': 'Dislike of or prejudice against people from other countries.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The rise of xenophobia is a worrying trend.',
                'ipa_pronunciation': '/ˌzenəˈfoʊbiə/'
            },
            {
                'word': 'yoke',
                'definition': 'A wooden crosspiece that is fastened over the necks of two animals and attached to the plow or cart that they are to pull.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The farmer placed the yoke on the oxen.',
                'ipa_pronunciation': '/joʊk/'
            },
            {
                'word': 'zephyr',
                'definition': 'A soft gentle breeze.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'A gentle zephyr rustled the leaves.',
                'ipa_pronunciation': '/ˈzefər/'
            },
            {
                'word': 'anachronism',
                'definition': 'A thing belonging or appropriate to a period other than that in which it exists, especially a thing that is conspicuously old-fashioned.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The movie was full of anachronisms.',
                'ipa_pronunciation': '/əˈnækrənɪzəm/'
            },
            {
                'word': 'boondoggle',
                'definition': 'Work or activity that is wasteful or pointless but gives the appearance of having value.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The new project was a boondoggle that wasted millions of dollars.',
                'ipa_pronunciation': '/ˈbuːndɒɡl/'
            },
            {
                'word': 'circumlocution',
                'definition': 'The use of many words where fewer would do, especially in a deliberate attempt to be vague or evasive.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'The politician\'s speech was full of circumlocution.',
                'ipa_pronunciation': '/ˌsɜːrkəmləˈkjuːʃn/'
            },
            {
                'word': 'dichotomy',
                'definition': 'A division or contrast between two things that are or are represented as being opposed or entirely different.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'There is a dichotomy between the rich and the poor.',
                'ipa_pronunciation': '/daɪˈkɒtəmi/'
            },
            {
                'word': 'epiphany',
                'definition': 'A moment of sudden revelation or insight.',
                'difficulty': 'advanced',
                'part_of_speech': 'noun',
                'example_sentence': 'She had an epiphany that changed her life.',
                'ipa_pronunciation': '/ɪˈpɪfəni/'
            },
        ]

        created_count = 0
        updated_count = 0

        for word_data in words_data:
            word, created = Word.objects.update_or_create(
                word=word_data['word'],
                defaults={
                    'definition': word_data['definition'],
                    'difficulty': word_data['difficulty'],
                    'part_of_speech': word_data['part_of_speech'],
                    'example_sentence': word_data['example_sentence'],
                    'ipa_pronunciation': word_data.get('ipa_pronunciation', ''),
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {word.word}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {word.word}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new words, updated {updated_count} existing words.'
            )
        )
