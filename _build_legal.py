#!/usr/bin/env python3
"""Build /terms/ and /privacy/ from the shared site shell.

Why these pages exist on OUR site rather than linking out to Arlo:
the footer used to point at www.the-training-centre.com/w/uk/{termsandconditions,privacypolicy},
which is the Arlo-hosted site. Clicking them dropped the visitor onto the OLD site,
complete with the old header and navigation (client raised this 30 Jul 2026), and after
the DNS cutover those paths would not exist on the new site at all.

The wording below is John's own, lifted verbatim from those two Arlo pages on 30 Jul 2026.
Do not reword it. It is legal copy - if it needs to change, it changes at John's instruction.
(Known source typos left untouched on purpose: "itslef", "event,,", "IS0". Flagged to John.)

Regenerate:  python _build_legal.py
"""
import re
import pathlib

HERE = pathlib.Path(__file__).parent
SHELL = HERE / "about" / "index.html"

# ---------------------------------------------------------------- shell parts
src = SHELL.read_text(encoding="utf-8")

head = src[: src.index("</head>")]
header = src[src.index("<body"): src.index("</header>") + len("</header>")]
tail = src[src.index('<footer class="bg-[#1E2B34]'):]

# /about/ is the active nav item in the shell; legal pages have no active item.
header = header.replace(
    '<a href="/about/" class="font-semibold text-[#0085B7]">About us</a>',
    '<a href="/about/" class="hover:text-[#0085B7]">About us</a>',
)

# Footer must point at these pages, not at Arlo.
tail = tail.replace(
    '<li><a href="https://www.the-training-centre.com/w/uk/termsandconditions" target="_blank" rel="noopener" class="hover:text-white">Terms &amp; conditions</a></li>',
    '<li><a href="/terms/" class="hover:text-white">Terms &amp; conditions</a></li>',
).replace(
    '<li><a href="https://www.the-training-centre.com/w/uk/privacypolicy" target="_blank" rel="noopener" class="hover:text-white">Privacy policy</a></li>',
    '<li><a href="/privacy/" class="hover:text-white">Privacy notice</a></li>',
)


def page(slug: str, title: str, desc: str, heading: str, standfirst: str, body: str) -> None:
    h = head
    h = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", h, flags=re.S)
    h = re.sub(
        r'<meta name="description" content=".*?">',
        f'<meta name="description" content="{desc}">',
        h,
        flags=re.S,
    )
    html = f"""{h}</head>
{header}

<main>
  <section class="bg-[#1E2B34] text-white">
    <div class="max-w-3xl mx-auto px-5 py-12 sm:py-16">
      <h1 class="font-display font-extrabold text-3xl sm:text-4xl leading-tight">{heading}</h1>
      <p class="mt-4 text-[#C8D2D9] leading-relaxed">{standfirst}</p>
    </div>
  </section>

  <section class="bg-white">
    <div class="max-w-3xl mx-auto px-5 py-12 sm:py-16 legal">
{body}
    </div>
  </section>
</main>

{tail}"""

    style = """
  .legal h2 { font-family: var(--font-display); font-weight: 800; color:#1E2B34; font-size:1.25rem; margin-top:2.5rem; margin-bottom:.75rem; }
  .legal h2:first-of-type { margin-top:0; }
  .legal h3 { font-weight:700; color:#1E2B34; margin-top:1.5rem; margin-bottom:.5rem; }
  .legal p { margin-bottom:1rem; line-height:1.75; }
  .legal ul { list-style:disc; padding-left:1.25rem; margin-bottom:1rem; }
  .legal ol { list-style:decimal; padding-left:1.25rem; margin-bottom:1rem; }
  .legal li { margin-bottom:.5rem; line-height:1.75; }
  .legal dt { font-weight:600; color:#1E2B34; margin-top:.75rem; }
  .legal dd { margin-left:0; line-height:1.75; }
  .legal a { color:#0085B7; text-decoration:underline; }
  .legal strong { color:#1E2B34; }
"""
    html = html.replace("  .card-pop", style.rstrip("\n") + "\n  .card-pop", 1)

    out = HERE / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(HERE)}  ({len(html):,} bytes)")


# ------------------------------------------------------------------- content
TERMS = """
      <h2>Background</h2>
      <p>These Terms and Conditions are the standard terms for the provision of services by The Training Centre Ltd, (TTC Ltd), is a Limited Company registered in England under number 15746376, whose registered address is Seedbed Business Centre, Vanguard Way, Shoeburyness, Essex, SS3 9QY.</p>

      <h2>1. Definitions and Interpretation</h2>
      <p>In these Terms and Conditions, unless the context otherwise requires, the following expressions have the following meanings:</p>
      <dl>
        <dt>&ldquo;Business Day&rdquo;</dt><dd>means any day other than a Saturday, Sunday or bank holiday;</dd>
        <dt>&ldquo;Calendar Day&rdquo;</dt><dd>means any day of the year;</dd>
        <dt>&ldquo;Contract&rdquo;</dt><dd>means the contract for the provision of Services, as explained in Clause 3;</dd>
        <dt>&ldquo;Deposit&rdquo;</dt><dd>means an advance payment made to Us under sub-Clause 5.5;</dd>
        <dt>&ldquo;Month&rdquo;</dt><dd>means a calendar month;</dd>
        <dt>&ldquo;Price&rdquo;</dt><dd>means the price payable for the Services;</dd>
        <dt>&ldquo;Services&rdquo;</dt><dd>means the services which are to be provided by Us to you as specified in your Order (and confirmed in Our Order Confirmation);</dd>
        <dt>&ldquo;Special Price&rdquo;</dt><dd>means a special offer price payable for Services which We may offer from time to time;</dd>
        <dt>&ldquo;Order&rdquo;</dt><dd>means your order for the Services requested;</dd>
        <dt>&ldquo;Order Confirmation&rdquo;</dt><dd>means Our acceptance and confirmation of your Order as described in Clause 3;</dd>
        <dt>&ldquo;We/Us/Our&rdquo;</dt><dd>means TTC Ltd</dd>
        <dt>&ldquo;Re-Registration&rdquo;</dt><dd>means us moving you to alternative course dates</dd>
        <dt>&ldquo;Registration Cancellation&rdquo;</dt><dd>means only that we have moved you from a particular set of delivery dates</dd>
        <dt>&ldquo;Cancellation&rdquo;</dt><dd>means that we have cancelled both your registration and the Course itself</dd>
      </dl>
      <p>Each reference in these Terms and Conditions to &ldquo;writing&rdquo; and any similar expression includes electronic communications whether sent by e-mail, text message, fax or other means.</p>

      <h2>2. Information About Us</h2>
      <p>TTC Ltd registered in England under number 15746376.</p>
      <p>Our VAT number is GB476426465</p>
      <p>Website address &ndash; www.the-training-centre.com</p>

      <h2>3. The Contract</h2>
      <p>These Terms and Conditions govern the sale and provision of Services by Us and will form the basis of the Contract between Us and you. Before submitting an Order, please ensure that you have read these Terms and Conditions carefully. If you are unsure about any part of these Terms and Conditions, please ask Us for clarification.</p>
      <p>Nothing provided by us including, but not limited to, sales and marketing literature, price lists and other documents constitutes a contractual offer capable of acceptance. Your Order constitutes a contractual offer that We may, at our discretion, accept.</p>
      <p>A legally binding contract between Us and you will be created upon our acceptance of your Order, indicated by Our Order Confirmation. Order Confirmations will be provided in writing at Point of Sale.</p>
      <p>We shall ensure that the following information is given or made available to you prior to the formation of the Contract between Us and you, save for where such information is already apparent from the context of the transaction:</p>
      <ul>
        <li>The main characteristics of the Services;</li>
        <li>Our identity (set out above in Clause 2) and contact details (as set out below in Clause 11);</li>
        <li>The total Price for the Services including VAT or, if the nature of the Services is such that the Price cannot be calculated in advance, the manner in which it will be calculated;</li>
        <li>The arrangements for payment, performance and the time by which (or within which) We undertake to perform the Services;</li>
        <li>Our complaints handling policy;</li>
        <li>Where applicable, details of after-sales services and commercial guarantees;</li>
        <li>The duration of the Contract, where applicable, or if the Contract is of indeterminate duration or is to be extended automatically, the conditions for terminating the Contract.</li>
      </ul>

      <h2>4. Orders</h2>
      <p>All Orders for Services made by you will be subject to these Terms and Conditions.</p>
      <p>You may change your Order at any time before We begin providing the Services by contacting Us. [Requests to change Orders do not need to be made in writing.]</p>
      <p>If your Order is changed we will inform you of any change to that order in writing.</p>
      <p>If you are deemed to be a Consumer, You may cancel your Order within 7 days of placing it. If you have already made any payments to us (including, but not limited to a Deposit), subject to our Cancellation terms, the payment(s) will be refunded as soon as is reasonably possible, and in any event within 14 Calendar Days of Our acceptance of your cancellation. [If you request that your Order be cancelled, you must confirm this in writing.] If you wish to cancel the Services after this time period, or once we have begun providing the Services, please refer to the Cancellations Section. If you are not deemed a Consumer, you will not be able to cancel your services once you are under Contract, instead, we will offer you a place on a further similar course, subject to us meeting minimum delegate numbers. This is at our discretion.</p>
      <p>We may cancel your Order at any time before we begin providing the Services due to the unavailability of required personnel or materials, or due to the occurrence of an event outside of our reasonable control. If such cancellation is necessary, we will inform you as soon as is reasonably possible. If you have made any payments to us (including, but not limited to the Deposit), the payment(s) will be refunded as soon as is reasonably possible, and in any event within 14 Calendar Days of us informing you of the cancellation. Cancellations will be confirmed in writing. This notification will state that both your Registration and Course has been cancelled.</p>

      <h2>5. Price and Payment</h2>
      <p>The Price of the Services will be that shown to be in place at the time of your order. If the Price shown in your order differs from our current Price we will inform you upon receipt of your Order.</p>
      <p>If we quote a Special Price which is different to the Price shown in our current website, the Special Price will be valid for 7 days or, if the Special Price is part of an advertised special offer, for the period shown in the advertisement. Orders placed during this period will be accepted at the Special Price even if we do not accept the Order until after the period has expired.</p>
      <p>Our Prices may change at any time but these changes will not affect Orders that we have already accepted.</p>
      <p>All Prices exclude VAT. If the rate of VAT changes between the date of your Order and the date of your payment, we will adjust the rate of VAT that you must pay. Changes in VAT will not affect any Prices where we have already received payment in full from you.</p>
      <p>The total balance of the Price is payable prior to delivery of the services. If you have chosen to Pay by Invoice, the terms and conditions for payment will be noted on the Invoice.</p>
      <p>We accept the following methods of payment:</p>
      <ul>
        <li>Stripe for Credit or debit Cards</li>
        <li>Pay by Invoice</li>
        <li>Pay by Direct Debit</li>
      </ul>
      <p>If you do not make payment to us by the due date (as shown in/on your Invoice), you may not be entitled to attend any agreed training or may be moved to subsequent training dates, where applicable.</p>
      <p>The provisions of sub-Clause 6 will not apply if you have promptly contacted us to dispute an invoice in good faith.</p>

      <h2>6. Providing the Services</h2>
      <p>As required by law, we will provide the Services with reasonable skill and care, consistent with best practices and standards in the industry, and in accordance with any information provided by Us about the Services and about Us. Our Service provision includes the format in which we deliver, such as Classroom, Live Online and e-learning.</p>
      <p>We will begin providing the Services on the date and format confirmed in Our Order Confirmation. The Services cover only the period specified, however, if we change the format, we may also change the dates. If this happens, we will always aim to deliver to you within the same timeframe initially. if this is not possible, we will offer you multiple alternative dates and delivery formats.</p>
      <p>We will make every reasonable effort to deliver the Services on time (and in accordance with your Order). We cannot, however, be held responsible for any delays if an event outside of Our control occurs. Please see the Force Majeure section for events outside of Our control.</p>
      <p>If We require any information or action from you in order to provide the Services, we will inform you of this as soon as is reasonably possible. Examples of what we may require include: special needs related to our duty of care to you.</p>
      <p>If the information or action required of you is delayed, incomplete or otherwise incorrect, we will not be responsible for any delay caused as a result. If additional work is required from Us to correct or compensate for a mistake made as a result of incomplete or otherwise incorrect information or action on your part, we may charge you a reasonable additional sum for that work.</p>
      <p>In certain circumstances, for example where there is a delay in you sending Us information or taking action required under sub-Clause 6.5, We may suspend the Services (and will inform you of that suspension in writing).</p>
      <p>In certain circumstances, for example where We encounter a technical problem, we may need to suspend the Services in order to resolve the issue. Unless the issue is an emergency and requires immediate attention, we will inform you in advance in writing before suspending the Services.</p>
      <p>If the Services are suspended under sub-Clauses 7.7 or 7.8, you will not be required to pay for them during the period of suspension.</p>
      <p>If you do not pay Us for the Services as required by Clause 6, We may suspend the Services until you have paid all outstanding sums due. If this happens, we will inform you in writing.</p>
      <p>If we have encountered costs as a result of your booking, we reserve the right to recover these costs in the event that you cancel your services.</p>

      <h2>7. Problems with the Services and Your Legal Rights</h2>
      <p>We always use reasonable efforts to ensure that provision of our Services is trouble-free. If, however, there is a problem with the Services We request that you inform Us as soon as is reasonably possible [you do not need to contact Us in writing].</p>
      <p>We will use reasonable efforts to remedy problems with the Services as quickly as is reasonably possible and practical.</p>
      <p>We will not charge you for remedying problems under this Clause 8 where the problems have been caused by Us, any of our agents or employees or sub-contractors or where nobody is at fault. If We determine that a problem has been caused by incorrect or incomplete information or action provided or taken by you, sub-Clause 7.6 will apply and we may charge you for remedial work.</p>
      <p>As a consumer, you have certain legal rights with respect to the purchase of services. For full details of your legal rights and guidance on exercising them, it is recommended that you contact your local Citizens Advice Bureau or Trading Standards Office. If We do not perform the Services with reasonable skill and care, you have the right to request repeat performance or, if that is not possible or done within a reasonable time without inconvenience to you, you have the right to a reduction in price. If the Services are not performed in line with information that We have provided about them, you also have the right to request repeat performance or, if that is not possible or done within a reasonable time without inconvenience to you (or if Our breach concerns information about Us that does not relate to the performance of the Services), you have the right to a reduction in price. If for any reason We are required to repeat the Services in accordance with your legal rights, we will not charge you for the same and We will bear any and all costs of such repeat performance. In cases where a price reduction applies, this may be any sum up to the full Price and, where you have already made payment(s) to Us, may result in a full or partial refund. Any such refunds will be issued without undue delay (and in any event within 14 calendar days starting on the date on which We agree that you are entitled to the refund) and made via the same payment method originally used by you unless you request an alternative method. In addition to your legal rights relating directly to the Services, you also have remedies if We use materials that are faulty or incorrectly described. Please note you may not be deemed to be a consumer, depending on the type of service requested, or for the following reasons - a &lsquo;consumer&rsquo; is &ldquo;an individual acting for purposes that are wholly or mainly outside that individual&rsquo;s trade, business, craft or profession.&rdquo; If you fall into this category, elements of this clause will not apply. You may in fact be deemed a Trader - A &lsquo;trader&rsquo; is defined as &ldquo;a person acting for purposes relating to that person&rsquo;s trade, business, craft or profession, whether acting personally or through another person acting in the trader&rsquo;s name or on the trader&rsquo;s behalf.&rdquo;</p>

      <h2>8. Our Liability</h2>
      <p>We will be responsible for any foreseeable loss or damage that you may suffer as a result of Our breach of these Terms and Conditions or as a result of Our negligence (including that of Our employees, agents or sub-contractors). Loss or damage is foreseeable if it is an obvious consequence of the breach or negligence or if it is contemplated by you and Us when the Contract is created. We will not be responsible for any loss or damage that is not foreseeable.</p>
      <p>We provide Services for private use only. You are not permitted to make use of our materials or services in a Commercial, Business or industrial manner [(including resale)]. You are not permitted to replicate any materials provided to you. By making your Order, you agree that you will not use the Services for such purposes. We will not be liable to you for any loss of profit, loss of business, interruption to business or for any loss of business opportunity.</p>
      <p>If We are providing Services in your property and We cause any damage, we will make good that damage at no additional cost to you. We are not responsible for any pre-existing faults or damage in or to your property that We may discover while providing the Services.</p>
      <p>Nothing in these Terms and Conditions seeks to exclude or limit Our liability for death or personal injury caused by Our negligence (including that of Our employees, agents or sub-contractors); or for fraud or fraudulent misrepresentation.</p>
      <p>Nothing in these Terms and Conditions seeks to exclude or limit Our liability for failing to perform the Services with reasonable care and skill or in accordance with information provided by Us about the Services or about Us.</p>
      <p>Nothing in these Terms and Conditions seeks to exclude or limit Your legal rights as a consumer. For more details of Your legal rights, please refer to Your local Citizens Advice Bureau or Trading Standards Office.</p>

      <h2>9. Events Outside of Our Control (Force Majeure)</h2>
      <p>We will not be liable for any failure or delay in performing Our obligations where that failure or delay results from any cause that is beyond Our reasonable control. Such causes include, but are not limited to: power failure, internet service provider failure, strikes, lock-outs or other industrial action by third parties, riots and other civil unrest, fire, explosion, flood, storms, earthquakes, subsidence, acts of terrorism (threatened or actual), acts of war (declared, undeclared, threatened, actual or preparations for war), epidemic or other natural disaster, or any other event that is beyond Our reasonable control.</p>
      <p>If any event described under this Clause 9 occurs that is likely to adversely affect Our performance of any of Our obligations under these Terms and Conditions:</p>
      <ul>
        <li>We will inform you as soon as is reasonably possible;</li>
        <li>Our obligations under these Terms and Conditions may be suspended, subject to the event itslef, and any time limits that we are bound by will be extended accordingly</li>
      </ul>
      <p>We will inform you when the event outside of Our control is over and provide details of any new dates, times or availability of Services as necessary.</p>
      <p>If an event outside of Our control occurs and you wish to cancel the Contract, you may only do so if you are deemed a Consumer, in accordance with your right to Cancel under sub-Clause 10.3.3. For non-consumer clients, we will always reschedule our events or provide an alternative delivery format. If you are deemed a Consumer, any refunds due to you as a result of a cancellation will be paid to you as soon as is reasonably possible, and in any event within 14 Calendar Days of Our acceptance of your cancellation notice.</p>
      <p>If the event outside of Our control continues for more than 26 weeks and we cannot agree an alternative delivery format, we may choose to cancel the Contract in accordance with Our right to cancel under sub-Clause 11.4.3 and inform you of the cancellation. Any refunds due to you as a result of that cancellation will be paid to you as soon as is reasonably possible, and in any event within 14 Calendar Days of Our cancellation notice.</p>

      <h2>10. Cancellation</h2>
      <p>If you are deemed a Consumer and you wish to cancel your Order for the Services before the Services begin, you may do so only up to and including 7 days after making the booking. This is not the case if we have incurred costs as a result of your booking. In this event, all costs will be deducted from any refund due to you, in the event you do not wish to reschedule. This is also not possible if you are not deemed a &ldquo;consumer&rdquo;. If you are not deemed a Consumer, we will either transfer you to another set of course dates, or offer you services up to the value of your booked course. The same consideration applies if you seek to cancel after the 7 day post booking period.</p>
      <p>Once we have begun (incurred costs in) providing the Services, you are no longer free to cancel or amend the Services. If it is not possible for you to attend your scheduled event,, we may offer you a credit towards any future events, subject to any costs we may have incurred. We will always endeavour to offer you a place on the next confirmed delivery dates or provide our services in an alternative format, where possible.</p>
      <p>If any of the following occur, you may cancel the Services and the Contract immediately by giving us written notice. If you have made any payment to us for any Services we have not yet provided, these sums will be refunded to you as soon as is reasonably possible, and in any event within 14 Calendar Days of our acceptance of your cancellation, subject to our Cancellation policies noted above. If we have provided Services that you have not yet paid for, the sums due will be deducted from any refund due to you or, if no refund is due, we will invoice you for those sums and you will be required to make payment per the terms agreed. If you cancel because of our breach, you will not be required to make any payments to us. You will not be required to give notice in these circumstances:</p>
      <ol type="a">
        <li>We have breached the Contract in any material way and have failed to remedy that breach within 7 days of you asking us to do so in writing; or</li>
        <li>We enter into liquidation or have an administrator or receiver appointed over Our assets; or we are unable to provide the Services due to an event outside of our control (as under sub-Clause 10.2.4); or</li>
        <li>We change these Terms and Conditions to your material disadvantage.</li>
      </ol>
      <p>We may cancel your Order for the Services before the Services begin under the following circumstances;</p>
      <p>Once we have begun providing the Services, we may cancel the Services and the Contract at any time by giving you written notice. If you have made any payment to us for any Services we have not yet provided, these sums will be refunded to you as soon as is reasonably possible, and in any event within 14 Calendar Days of Our cancellation notice. If we have provided Services that you have not yet paid for, we will invoice you for those sums and you will be required to make payment in accordance with Clause 6.</p>
      <p>For the purposes of this Clause 10 (and in particular, sub-Clauses 10.3.1 and 10.6.2) a breach of the Contract will be considered &lsquo;material&rsquo; if it is not minimal or trivial in its consequences to the terminating party (i.e. you under sub-Clause 10.3.1 and Us under sub-Clause 10.6.2). In deciding whether or not a breach is material no regard will be had to whether it was caused by any accident, mishap, mistake or misunderstanding.</p>

      <h2>11. Communication and Contact Details</h2>
      <p>If you wish to contact Us, you may do so by telephone at <a href="tel:+442038589207">0203 858 9207</a> or by email at <a href="mailto:info@the-training-centre.com">info@the-training-centre.com</a>.</p>
      <p>In certain circumstances you must contact us in writing (when cancelling an Order, for example, or exercising your right to cancel the Services). When contacting us in writing you may use the following methods:</p>
      <ol type="a">
        <li>Contact Us by email at <a href="mailto:info@the-training-centre.com">info@the-training-centre.com</a>; or</li>
        <li>Contact Us by pre-paid post at Seedbed Business Centre, Shoeburyness, SS3 9QY</li>
      </ol>

      <h2>12. Complaints and Feedback</h2>
      <p>We always welcome feedback from Our customers and, whilst we always use all reasonable endeavours to ensure that your experience as a customer of Ours is a positive one, we nevertheless want to hear from you if you have any cause for complaint.</p>
      <p>All complaints are handled in accordance with Our complaints handling policy and procedure.</p>
      <p>If you wish to complain about any aspect of your dealings with Us, including, but not limited to, these Terms and Conditions, the Contract, or the Services, please contact Us in one of the following ways:</p>
      <ol type="a">
        <li>In writing, addressed to Administrative Services, TTC Ltd, Head Office.</li>
        <li>By email, addressed to John McGlone at <a href="mailto:john.mcglone@the-training-centre.com">john.mcglone@the-training-centre.com</a>;</li>
        <li>By contacting us by telephone on <a href="tel:+442038589207">0203 858 9207</a></li>
      </ol>

      <h2>13. How We Use Your Personal Information (Data Protection)</h2>
      <p>All personal information that we may use will be collected, processed, and held in accordance with the provisions of EU Regulation 2016/679 General Data Protection Regulation (&ldquo;GDPR&rdquo;) and your rights under the GDPR.</p>
      <p>For complete details of Our collection, processing, storage, and retention of personal data including, but not limited to, the purpose(s) for which personal data is used, the legal basis or bases for using it, details of your rights and how to exercise them, and personal data sharing (where applicable), please refer to <a href="/privacy/">Our Privacy Notice</a>.</p>

      <h2>14. Other Important Terms</h2>
      <p>We may transfer (assign) Our obligations and rights under these Terms and Conditions (and under the Contract, as applicable) to a third party (this may happen, for example, if We sell Our business). If this occurs you will be informed by Us in writing. Your rights under these Terms and Conditions will not be affected and Our obligations under these Terms and Conditions will be transferred to the third party who will remain bound by them.</p>
      <p>You may not transfer (assign) your obligations and rights under these Terms and Conditions (and under the Contract, as applicable) without Our express written permission.</p>
      <p>The Contract is between you and Us. It is not intended to benefit any other person or third party in any way and no such person or party will be entitled to enforce any provision of these Terms and Conditions.</p>
      <p>If any of the provisions of these Terms and Conditions are found to be unlawful, invalid or otherwise unenforceable by any court or other authority, that / those provision(s) shall be deemed severed from the remainder of these Terms and Conditions. The remainder of these Terms and Conditions shall be valid and enforceable.</p>
      <p>No failure or delay by Us in exercising any of Our rights under these Terms and Conditions means that We have waived that right, and no waiver by Us of a breach of any provision of these Terms and Conditions means that We will waive any subsequent breach of the same or any other provision.</p>

      <h2>15. Governing Law and Jurisdiction</h2>
      <p>These Terms and Conditions, the Contract, and the relationship between you and Us (whether contractual or otherwise) shall be governed by and construed in accordance with the law of England &amp; Wales.</p>
      <p>As a consumer, you will benefit from any mandatory provisions of the law in your country of residence. Nothing in Sub-Clause 15.1 above takes away or reduces your rights as a consumer to rely on those provisions</p>
      <p>Any dispute, controversy, proceedings or claim between you and Us relating to these Terms and Conditions, the Contract, or the relationship between you and Us (whether contractual or otherwise) shall be subject to the jurisdiction of the courts of England, Wales, Scotland, or Northern Ireland, as determined by your residency.</p>
"""

PRIVACY = """
      <h2>Our Commitment</h2>
      <p>The Training Centre, hereafter known as TTC Ltd, takes your privacy seriously. Please read this Privacy Notice (&ldquo;Notice&rdquo;) to learn more about how we collect, use, disclose and store information when you access or use our Website or Services or contact us a different way. We gather various types of information, including information that identifies you as an individual (Personal Information). This is explained below.</p>

      <h2>What information does TTC Ltd collect?</h2>
      <p>When you use our Website, we may collect Personal Information that you chose to provide to us. For example, on our &ldquo;Contact Us,&rdquo; page or request to download a resource, you provide us contact information.</p>
      <p>When you use our Services, we collect information directly from you such as names, email addresses, postal addresses, phone numbers, job titles, in order to set up and provide you the Services.</p>

      <h2>How do we use the information?</h2>
      <p>When you provide information to us through our Website, we may use the information to respond to your inquiries, e.g., regarding certain products or Services or request to download a resource. We also use information to administer and improve our Website and to analyze use of the Website for marketing and advertising purposes and trend monitoring.</p>
      <h3>When you use our Services, we may use your information:</h3>
      <ul>
        <li>To establish and maintain responsible commercial relations and to provide ongoing Service. For example, when you request attendance at one of our Training Courses we collect your Personal Information to fulfil the course booking criteria.</li>
        <li>To contact you about your use of Services or fulfil your request for a downloadable resource,</li>
        <li>To meet legal and regulatory requirements. For example, we may collect Personal Information from you to satisfy government regulations, e.g., tax purposes,</li>
        <li>For any other purposes about which we will notify you.</li>
      </ul>

      <h2>Disclosure to Third Parties</h2>
      <p>We do not rent or sell your Personal Information. We may share and disclose information, including Personal Information about our customers in limited circumstances as described below. TTC Ltd transfers Personal Information to third parties such as service providers who perform tasks on our behalf such as for processing and storage purposes. These companies include, for example, our payment processing providers, website analytics companies, CRM and training service providers and email service providers.</p>
      <p>If TTC Ltd has received your Personal Information and subsequently transfers that information to a third party agent or service provider for processing, TTC Ltd will remain responsible by executing contracts requiring them to protect the privacy and confidentiality of the Personal Information provided to them for purposes of performing their functions for us. Unless we tell you differently and you consent, our agents do not have any right to use the Personal Information we share with them beyond what is necessary to assist us. We do not transfer your data to any third party country.</p>
      <p>Although very unlikely, in some instances, such as a legal proceeding or court order, we may be required to disclose certain information to authorities. Only the information specifically requested is disclosed and we shall take precautions to satisfy ourselves that the authorities who are making the request have legitimate grounds to do so.</p>
      <p>In the event TTC Ltd is merged with or is acquired by another organization, we will make every reasonable effort to notify you if we share with the merging or acquiring organization some or all of your Personal Information.</p>

      <h2>Security for Privacy</h2>
      <p>TTC Ltd protects Personal Information against unauthorized access. TTC Ltd has organizational, technical and physical security safeguards in place to protect Personal Information. Personal Information shall be protected by security safeguards appropriate to the sensitivity of the information.</p>
      <p>Notwithstanding that, TTC Ltd has security safeguards in place to protect Personal Information, Customers are always encouraged to take measures to protect themselves against unintended intrusions to their personal privacy (i.e., maintain access pass codes and/or PINs in a confidential manner).</p>

      <h2>What choices do I have?</h2>
      <p>You can always opt not to disclose information to us. Please note that some information may be needed to register with us or to take advantage of some of our features.</p>

      <h2>Accessing and Updating your Personal Information</h2>
      <p>To review and update your Personal Information to ensure it is accurate, contact <a href="mailto:info@the-training-centre.com">info@the-training-centre.com</a>. TTC Ltd will make commercially reasonable efforts to provide you reasonable access to any of your personal information we maintain within 30 days of your access request so that you can review, make corrections, or request deletion of your data. If we cannot honor your request within the 30-day period, we will tell you when we will be able to provide access. In the unlikely event that we are not able to provide you access to this information, we will explain why we cannot do so.</p>

      <h2>Complaints or Questions regarding this Privacy Notice</h2>
      <p>Individuals may address their privacy related concerns or complaints by contacting TTC Ltd at <a href="mailto:info@the-training-centre.com">info@the-training-centre.com</a></p>
      <p>Every privacy-related complaint will be acknowledged, recorded and investigated, and the results of the investigation will be provided. If a complaint is found to be justified, appropriate measures will be taken.</p>
      <p>If you are a resident of the European Economic Area and have an unresolved privacy or personal information collection, use, or disclosure concern that we have not addressed satisfactorily, please be aware you can address your concern to the Information Commissioner&rsquo;s Office, who may decide to further investigate the matter. TTC Ltd will always fully cooperate with any regulatory request. If any aspect of this privacy Notice causes concern or if we cannot answer your specific requirement to your satisfaction, please contact the Information Commissioner&rsquo;s Office on <a href="mailto:info@ico.org.uk">info@ico.org.uk</a></p>
"""

page(
    "terms",
    "Terms &amp; Conditions | The Training Centre",
    "The standard service terms and conditions for training delivered by The Training Centre Ltd, including orders, price and payment, cancellation and your legal rights.",
    "Terms &amp; conditions",
    "The standard terms for the provision of services by The Training Centre Ltd. Please read them before placing an order.",
    TERMS,
)

page(
    "privacy",
    "Privacy Notice | The Training Centre",
    "How The Training Centre Ltd collects, uses, discloses and stores your personal information, your rights under the GDPR, and how to contact us about them.",
    "Privacy notice",
    "How we collect, use, disclose and store information when you use our website or our services.",
    PRIVACY,
)
