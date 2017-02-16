package uk.gov.ons.ras.json;

/**
 * This class intentionally has public fields because it is a pure data record, with no state.
 */
public class CollectionInstrumentJson {

    /** The public collection instrument reference identifier. */
    public String id;

    /** The survey identifier for the survey this instrument relates to. */
    public String surveyId;

    /** The URN. Just because. */
    public String urn;

    /** The type of this collection instrument, which should be questionnaire or spreadsheet. */
    public String type;

    /** A link to access the collection instrument. */
    public String link;

    /** A custom DSL scheme for future logic that will identify which collection instrument is applicable. */
    // We'll expand on this
    public String classifiers;
}
