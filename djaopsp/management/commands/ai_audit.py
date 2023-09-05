# Copyright (c) 2023, DjaoDjin inc.
# All rights reserved.

"""
Command to analyze ESG supportive evidence and answer questions
"""

import io, os
import openai
import ocrmypdf
import requests
import tiktoken
from PyPDF2 import PdfReader
from django.core.management.base import BaseCommand

from survey.api.sample import update_or_create_answer
from survey.models import Sample, Unit, Question
from survey.utils import datetime_or_now

from ...utils import get_supporting_documents

openai.api_key = os.environ['OPENAI_API_KEY']

ai_model = 'gpt-4'
token_limit = 8000
# derived by trial & error
openapi_prompt_len = 2000

dummy_openapi_responses = ["1 - Yes - The company has a set of defined criteria for the reporting of Greenhouse gas (GHG) emissions and water consumption including Scope 1, Scope 2 and Scope 3 emissions, as well as the methodologies for their calculations. The report covers the year ended December 31, 2017.\n2 - n/a\n3 - n/a\n4 - Yes - The company reports internally on the key ESG issue of greenhouse gas emissions and water consumption as shown in the provided document. The report demonstrates progress towards their goals with detailed accounting for their emissions.\n5 - Yes - The company's reporting of GHG emissions and water consumption adheres to numerous reputable reporting standards including: The Greenhouse Gas Protocol by the World Resources Institute (WRI)/World Business Council for Sustainable Development (WBCSD), The UK Department for Environment Food & Rural Affairs (DEFRA) 2012 guidance, Intergovernmental Panel on Climate Change (IPCC) Fourth Assessment Report (2007), and The Climate Registry General Reporting Protocol.\n6 - n/a\n7 - n/a\n8 - n/a\n9 - n/a\n10 - n/a\n11 - n/a\n12 - n/a\n13 - n/a\n14 - n/a\n15 - n/a\n16 - n/a\n17 - n/a\n18 - n/a\n19 - n/a\n20 - n/a\n21 - n/a\n22 - n/a\n23 - n/a\n24 - n/a\n25 - n/a\n26 - n/a\n27 - n/a\n28 - n/a\n29 - n/a\n30 - n/a\n31 - n/a\n32 - n/a\n33 - n/a\n34 - n/a\n35 - n/a\n36 - n/a\n37 - n/a\n38 - n/a\n39 - n/a\n40 - n/a\n41 - n/a\n42 - n/a\n43 - Yes - The company reports total Scope 1 GHG emissions publicly. The amount reported for the year ended December 31, 2017 is 376,735 Metric tonnes of CO2e\n44 - n/a\n45 - Yes - The company reports total Scope 2 GHG emissions publicly. The amount reported for the year ended December 31, 2017 is 4,522,261 Metric tonnes of CO2e\n46 - n/a\n47 - Yes - The company reports total Scope 3 GHG emissions publicly, solely related to corporate business travel. The amount reported for the year ended December 31, 2017 is 69,271 Metric tonnes of CO2e\n48 - n/a\n49 - Yes - The company reports water withdrawn and consumed publicly. The amount reported for the year ended December 31, 2017 is 2.39 Billions of gallons\n50 - n/a\n51 - n/a\n52 - n/a\n53 - n/a\n54 - n/a\n55 - n/a\n56 - n/a\n57 - n/a\n58 - n/a\n59 - n/a\n60 - n/a\n61 - n/a\n62 - n/a\n63 - n/a\n64 - n/a\n65 - n/a\n66 - n/a\n67 - n/a\n68 - n/a\n69 - n/a\n70 - n/a\n71 - n/a\n72 - n/a\n73 - n/a\n74 - n/a", '1. - n/a\n2. - n/a\n3. - n/a\n4. - n/a\n5. - n/a\n6. - n/a\n7. - n/a\n8. - n/a\n9. - n/a\n10. - n/a\n11. - n/a\n12. - n/a\n13. - n/a\n14. - n/a\n15. - n/a\n16. - n/a\n17. - n/a\n18. - n/a\n19. - n/a\n20. - n/a\n21. - n/a\n22. - n/a\n23. - n/a\n24. - n/a\n25. - n/a\n26. - n/a\n27. - n/a\n28. - n/a\n29. - n/a\n30. - n/a\n31. - n/a\n32. - n/a\n33. - n/a\n34. - n/a\n35. - n/a\n36. - n/a\n37. - n/a\n38. - n/a\n39. - n/a\n40. - n/a\n41. - n/a\n42. - n/a\n43. - n/a\n44. - n/a\n45. - n/a\n46. - n/a\n47. - n/a\n48. - n/a\n49. - Yes - "Water consumption (in billions of gallons) is calculated for all sites that use municipal water1 within Verizon’s operational control based on:"\n50. - n/a\n51. - n/a\n52. - n/a\n53. - Yes - "Stationary energy cutoff: \uf0a7 Domestic billed data received as of April 29, 2018 \uf0a7 International billed data received as of April 30, 2018 o Estimated electricity data as of May 16, 2018"\n54. - n/a\n55. - n/a\n56. - n/a\n57. - n/a\n58. - n/a\n59. - n/a\n60. - n/a\n61. - n/a\n62. - n/a\n63. - n/a\n64. - n/a\n65. - n/a\n66. - n/a\n67. - n/a\n68. - n/a\n69. - n/a\n70. - n/a\n71. - n/a\n72. - n/a\n73. - n/a\n74. - n/a']

def get_tokens(contents):
    encoding = tiktoken.encoding_for_model(ai_model)
    return encoding.encode(contents)

def extract_text_from_text_pdf(stream):
    contents = ''

    reader = PdfReader(stream)
    for page in reader.pages:
        text = page.extract_text()
        contents += f"{text}\n"
    return contents.strip()

def extract_text_from_pdf(stream):
    treshold = 5
    contents = extract_text_from_text_pdf(stream)
    
    if len(contents) > treshold:
        return contents
    else:
        stream.seek(0)
        out_io = io.BytesIO()

        ocrmypdf.ocr(stream, out_io, deskew=True, force_ocr=True, language='eng')
        ocr_contents = extract_text_from_text_pdf(out_io)
        return ocr_contents

def fetch_resource(url):
    if not url.lower().strip().startswith('http'):
        raise Exception('Bad URL')
    res = requests.get(url)
    return io.BytesIO(res.content)

questions = {
    # Environment, Social & Governance (ESG) Strategy
    '/sustainability/governance/esg-strategy-heading/formalized-esg-strategy': 'Does this company have a formalized ESG strategy and performance targets that: \
    a) Define a future vision of ESG performance, \
    b) Are clear, actionable, and achievable, \
    c) Are resourced effectively, \
    d) Address material issues for the business?',

    '/sustainability/governance/esg-strategy-heading/assign-formal-authority': 'Has this company assigned formal responsibility for directing and overseeing ESG performance to top/executive management?',
    '/sustainability/governance/esg-strategy-heading/assign-point-person': 'Has this company designated a point person(s) responsible for implementing strategy and meeting targets?',
    '/sustainability/governance/esg-strategy-heading/report-internally': 'Does this company report internally, including to top management, on strategy: key ESG issues (revealed by materiality analysis), resiliency, risk, business continuity, progress toward goals, and plans/needs to address gaps towards your targets?',
    '/sustainability/governance/esg-strategy-heading/report-externally': 'Does this company report externally on strategy: program elements, key ESG issues and goals, challenges, resiliency, and continual improvement efforts in accordance with a reputable reporting standard (e.g. GRI, SASB, TCFD)?',
    '/sustainability/governance/esg-strategy-heading/report-3rd-party-verified': 'Does this company have ESG strategy and reports, targets, and Key Performance Indicators (KPIs) periodically (every 5 years or sooner) validated by an independent third party?',

    # Environment, Social & Governance (ESG) Materiality Assessment
    '/sustainability/governance/esg-assessment/systematic-rigorous-assessment': 'Has this company conducted a systematic, rigorous assessment to identify and prioritize material ESG impacts, issues and opportunities?',

    # Code of conducts and policies
    '/sustainability/governance/governance-policies/employee-code-of-conduct': 'Does this company have an Employee Code of Conduct?',
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-child-and-forced-labor': "Does this company's Employee Code of Conduct contain sections pertinent to Child and Forced Labor?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-corruption-and-bribery': "Does this company's Employee Code of Conduct contain sections pertinent to Corruption and bribery?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-discrimination': "Does this company's Employee Code of Conduct contain sections pertinent to Discrimination & harassment​?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-diversity-inclusion': "Does this company's Employee Code of Conduct contain sections pertinent to Diversity and inclusion?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-working-hours': "Does this company's Employee Code of Conduct contain sections pertinent to Working hours?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-confidentiality': "Does this company's Employee Code of Conduct contain sections pertinent to Confidentiality of information?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-conflicts-of-interest': "Does this company's Employee Code of Conduct contain sections pertinent to Conflicts of interest?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-antitrust': "Does this company's Employee Code of Conduct contain sections pertinent to Antitrust/anti-competitive practices?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-money-laundering': "Does this company's Employee Code of Conduct contain sections pertinent to Money-laundering and/or insider trading/dealing?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-safety': "Does this company's Employee Code of Conduct contain sections pertinent to Environment, health and safety?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-whistleblowing': "Does this company's Employee Code of Conduct contain sections pertinent to Whistleblowing?",
    '/sustainability/policies/employee-code-of-conduct-follow/employee-code-of-conduct-labor-unions': "Does this company's Employee Code of Conduct contain sections pertinent to Collective bargaining, labor unions?",
    '/sustainability/governance/governance-policies/supplier-code-of-conduct': 'Does this company have a Supplier Code of Conduct and/or Human Rights Policy in place?',
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-child-and-forced-labor': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Child and Forced Labor?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-corruption-and-bribery': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Corruption and bribery?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-discrimination': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Discrimination & harassment?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-diversity-inclusion': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Diversity and inclusion?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-working-hours': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Working hours?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-confidentiality': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Confidentiality of information?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-conflicts-of-interest': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Conflicts of interest?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-antitrust': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Antitrust/anti-competitive practices?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-money-laundering': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Money-laundering and/or insider trading/dealing?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-safety': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Environment, health and safety?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-whistleblowing': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to Whistleblowing?",
    '/sustainability/policies/supplier-code-of-conduct-follow/supplier-code-of-conduct-external-stakeholders': "Does this company's Supplier Code of Conduct and/or Human Rights Policy contain sections pertinent to External stakeholder human rights?",

    # Sourcing practices
    '/sustainability/governance/governance-policies/sourcing-practices/conflict-minerals-in-products': 'Are there any conflict minerals or additional minerals of concern (including: cobalt, tin, tantalum, tungsten, or gold) in the product(s) that this company manufactures, subcontracts, or sells?',
    '/sustainability/governance/governance-policies/sourcing-practices/conflict-minerals-in-products-report': 'If there are any conflict minerals or additional minerals of concern (including: cobalt, tin, tantalum, tungsten, or gold) in the product(s) that this company manufactures, subcontracts, or sells - Has this company published a due diligence report on conflict minerals (including or not including cobalt)?',
    '/sustainability/governance/governance-policies/sourcing-practices/conflict-minerals-policy': 'Does this company have a policy related to sourcing minerals of concern (including: cobalt, tin, tantalum, tungsten, or gold)?',
    '/sustainability/governance/governance-policies/sourcing-practices/high-risk-regions-sourcing-products': 'Does this company source any of the specific materials, minerals, or products from the related countries listed on the Department of Labor "List of Goods Produced by Child Labor or Forced Labor" (available here https://www.dol.gov/agencies/ilab/reports/child-labor/list-of-goods)?',
    '/sustainability/governance/governance-policies/sourcing-practices/high-risk-regions-sourcing-policy': 'Does this company have a policy related to sourcing materials from regions of concern?',

    # Environmental Management System Rigor
    '/sustainability/governance/environmental-management-rigor/env-system-in-place': 'Has this company implemented an environmental management system that conforms with a recognized international (e.g. ISO 14001) or local standard?',
    '/sustainability/governance/environmental-management-rigor/env-system-certified': 'Is the system certified to a recognized local or international standard?',
    '/sustainability/governance/environmental-management-rigor/env-system-audited': 'Is the system periodically (e.g. every 5 years) audited internally and by an independent third party?',

    # Environmental reporting
    '/sustainability/governance/environmental-reporting/environmental-fines': 'Has this company received or been responsible for a Notice of Violation (NOV), Consent Order or fine over USD $10,000 from an environmental agency, or an environmental event that required reporting to an environmental agency in the past 36 months?',

    # GHG Emissions reporting
    '/sustainability/governance/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-publicly-reported': 'Does this company report total Scope 1 GHG emissions publicly?',
    '/sustainability/governance/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-3rd-party-verified': "Have this company's Scope 1 GHG Emissions data been third-party verified within last 2 years?",
    '/sustainability/governance/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope2-publicly-reported': 'Does this company report total Scope 2 GHG emissions publicly?',
    '/sustainability/governance/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope2-3rd-party-verified': "Have this company's Scope 2 GHG emissions data been third-party verified within last 2 years?",
    '/sustainability/governance/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope3-publicly-reported': 'Does this company report total Scope 3 GHG emissions publicly?',
    '/sustainability/governance/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope3-3rd-party-verified': "Have this company's Scope 3 GHG emissions data been third-party verified within last 2 years?",

    # Water reporting
    '/sustainability/governance/environmental-reporting/water-reporting/water-publicly-reported': 'Does this company report water withdrawn, discharged and re-used publicy?',
    '/sustainability/governance/environmental-reporting/water-reporting/water-3rd-party-verified': 'Have water data been third-party verified within the last 2 years?',

    # Waste reporting
    '/sustainability/governance/environmental-reporting/waste-reporting/waste-publicly-reported': 'Does this company report waste generated and recycled publicly?',
    '/sustainability/governance/environmental-reporting/waste-reporting/waste-3rd-party-verified': 'Has the waste measurement methodology been third-party verified within the last 2 years?',

    # Energy reporting
    '/sustainability/governance/environmental-reporting/energy-reporting/energy-publicly-reported': 'Does this company report total Energy consumed publicly?',
    '/sustainability/governance/environmental-reporting/energy-reporting/energy-3rd-party-verified': 'Have Energy data been third-party verified within last 2 years?',

    # Social & Governance reporting
    '/sustainability/governance/social-reporting/governance-fines': 'Has this company had any significant code of conduct breaches including but not limited to breaches resulting in fines, class action lawsuits, or repeated breaches of Codes of Conduct in the past 36 months?',

    # Does this company report internally or externally Key Performance Indicators (KPIs) on
    '/sustainability/governance/social-reporting/social-kpis/kpi-diversity-discrimination-harassment': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Discrimination & Harassment?',
    '/sustainability/governance/social-reporting/social-kpis/kpi-diversity-of-employees': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Diversity of Employees?',
    '/sustainability/governance/social-reporting/social-kpis/kpi-diversity-of-board': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Diversity of Executive Leadership and/or Board?',
    '/sustainability/governance/social-reporting/social-kpis/kpi-recordable-incident-rate': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Recordable Incident Rate?',
    '/sustainability/governance/social-reporting/social-kpis/kpi-lost-time-case-rate': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Lost-time Case Rate?',
    '/sustainability/governance/social-reporting/social-kpis/kpi-dart-rate': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Days Away, Restricted, and Transfer (DART) Rate?',
    '/sustainability/governance/social-reporting/social-kpis/kpi-work-related-fatalities': 'Does this company report internally or externally Key Performance Indicators (KPIs) on Work-related Fatalities?',

    '/sustainability/governance/social-reporting/diverse-spend': 'Does this company have a target for diverse spend publicly communicated?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-disability-owned': 'If this company has a target for diverse spend, does this company define diverse suppliers as disability-owned businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-hubzone': 'If this company has a target for diverse spend, does this company define diverse suppliers as HUBZone businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-lgbt-owned': 'If this company has a target for diverse spend, does this company define diverse suppliers as LGBT-owned businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-minority-owned': 'If this company has a target for diverse spend, does this company define diverse suppliers as minority-owned businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-service-disable-owned': 'If this company has a target for diverse spend, does this company define diverse suppliers as service-disable veteran businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-small-revenue': 'If this company has a target for diverse spend, does this company define diverse suppliers as small businesses (by revenue)?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-small-employees': 'If this company has a target for diverse spend, does this company define diverse suppliers as small businesses (by employees)?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-small-disadvantaged': 'If this company has a target for diverse spend, does this company define diverse suppliers as small disadvantaged businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-veteran-owned': 'If this company has a target for diverse spend, does this company define diverse suppliers as veteran-owned businesses?',
    '/sustainability/targets/diverse-target/diverse-target-definition/diverse-definition-woman-owned': 'If this company has a target for diverse spend, does this company define diverse suppliers as woman-owned businesses?',

    '/sustainability/targets/diverse-target/diverse-target-verification': 'If this company has a target for diverse spend, does this company require third-party certification to verify a supplier diverse status?',
}

questions_list = list(questions.items())

questions_str = ''
for (idx, q) in enumerate(questions_list):
    questions_str += f"{idx+1}. {q[1]} [ANSWER HERE]\n"

prime = "You are an expert ESG (Environment, Social and Governance) auditor, you are producing ESG performance report of a specific company. \
        The report contains a set of questions that you have to answer with \"yes\" or \"n/a\". Each question is related to a specific ESG topic. \
        The company provided a document with data that has to be used to obtain the answers to the questions. \
        The document is a PDF file or a scanned image, you've already extracted the text from the document. \
        For each question, you need to analyze the document and look for information that can be used to answer the question. \
        The document might have or might not have enough information to answer the questions. \
        If you were able to find information in the document to answer a question, answer \"yes\" and include this information (and date of the information if applicable) in your answer. \
        If you weren't able to find information which would've helped you to answer a question, you should answer \"n/a\". \
        Return the report, in the report each question-answer must follow this format:\n\n\
        [Number] - [Answer] - [Supportive evidence (if answer is \"yes\")]\n\
        \n\n \
        Here's the list of questions you should answer:\n\n"
prime += questions_str
prime += "\n\nHere's the extracted text from the document that you have to analyze and use to answer the questions:\n\n"

def decode_tokens(tokens_list):
    encoding = tiktoken.encoding_for_model(ai_model)
    return [encoding.decode(tokens) for tokens in tokens_list]

def maybe_split_input_into_chunks(prime, evidence):
    prime_tokens = get_tokens(prime)
    evidence_tokens = get_tokens(evidence)
    prompt_len = len(prime_tokens) + len(evidence_tokens) + openapi_prompt_len
    if prompt_len <= token_limit:
        tokens = [evidence_tokens]
    else:
        chunk_len = token_limit-len(prime_tokens)-openapi_prompt_len
        res = []
        rem = evidence_tokens[:]
        while len(rem) > 0:
            res.append(rem[0:chunk_len])
            rem = rem[chunk_len:]
        tokens = res
    return decode_tokens(tokens)

def openapi_call(prime, evidence):
    outputs = []
    for chunk in evidence:
        completion = openai.ChatCompletion.create(
            model=ai_model,
            messages=[
                {"role": "system", "content": prime},
                {"role": "user", "content": chunk},
            ]
        )
        outputs.append(completion.choices[0].message['content'])
    return outputs

def map_responses_to_questions(responses, evidence_chunks, url):
    MIN_ANSWER_LEN = 3
    ANSWER_NOT_AVAILABLE = 'n/a'
    QUESTION_NUM_NOISE_OFFSET = 3

    result = {}
    for (chunk_idx, response) in enumerate(responses):
        answers = response.split('\n')
        # TODO we can potentially still use the response in
        # situations where there's less answers than there are
        # questions
        if len(answers) != len(questions_list):
            print("Can't map OpenAPI response to questions")
            continue
        for (question_idx, answer) in enumerate(answers):
            question_num_str = str(question_idx + 1)

            # we are not interested in blank or n/a answers
            if ANSWER_NOT_AVAILABLE in answer.lower() or len(answer.strip()) < MIN_ANSWER_LEN:
                continue
            # basic sanity checks to ensure we are mapping the right answer
            if question_num_str not in answer[0:len(question_num_str)+QUESTION_NUM_NOISE_OFFSET]:
                print("Can't map OpenAPI answer to question")
                continue

            question_path = questions_list[question_idx][0]
            if question_path not in result:
                result[question_path] = []

            result[question_path].append({
                'answer': answer.strip(),
                'chunk': evidence_chunks[chunk_idx],
                'source': url,
            })
    return result

def denormalize_answers_to_str(answers):
    # TODO we are currently ignoring the file chunk where
    # the answer was found
    result = ''
    for answer in answers:
        result += answer['answer']
        result += '\n\n Source:'
        result += answer['source']
        result += '\n\n ======== \n\n'
    return result

def persist_answers(oa_answers, sample, questions_objs):
    unit = Unit.objects.get(slug='chatgpt_answer')
    created_at = datetime_or_now()

    results = []

    for (question_path, answers) in oa_answers.items():
        question_obj = questions_objs[question_path]
        openai_answer = denormalize_answers_to_str(answers)

        datapoint = {
            'measured': openai_answer,
            'unit': unit
        }
        obj, _ = update_or_create_answer(datapoint=datapoint, sample=sample,
            question=question_obj, created_at=created_at)
        results.append(obj)
    
    return results

def process_file(url, debug=False):
    stream = fetch_resource(url)
    text = extract_text_from_pdf(stream)
    evidence_chunks = maybe_split_input_into_chunks(prime, text)
    if not debug:
        responses = openapi_call(prime, evidence_chunks)
        print(responses)
    else:
        responses = dummy_openapi_responses
    results = map_responses_to_questions(responses, evidence_chunks, url)
    
    return results

class Command(BaseCommand):
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('sample', action='store',
            help='sample slug')
        parser.add_argument('--dry-run', action='store_true',
            dest='dry_run', default=False,
            help='Do not make OpenAPI calls')


    def handle(self, *args, **options):
        # files = get_supporting_documents([options['sample']])
        files = [
            'http://www.corporatereport.com/verizon/Independent_Accountant_Review_Report_FINAL.pdf',
            # 'https://sustainability.wm.com/downloads/WM_2018_Verification_Assurance_Letter.pdf',
            # 'https://assets.siemens-energy.com/siemens/assets/api/uuid:49bc59fb-7af0-47fc-a764-a3550d4153dc/siemens-energy-sustainability-report-2022.pdf?ste_sid=b611336d86f0c6ef4d1d8836f39ed03d'
        ]

        sample = Sample.objects.get(slug=options['sample'])
        questions_objs = {q.path: q for q in Question.objects.all()}

        for file in files:
            results = process_file(file, debug=options['dry_run'])
            persist_answers(results, sample, questions_objs)