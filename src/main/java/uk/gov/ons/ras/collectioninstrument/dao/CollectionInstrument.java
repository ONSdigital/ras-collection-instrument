package uk.gov.ons.ras.collectioninstrument.dao;

import java.util.Map;

/**
 * Represents the Json stored in the content column in the database.
 */
public class CollectionInstrument {
    public String reference;
    public String urn;
    public String ciType;
    public String surveyId;
    public Map<String, String> classifiers;
}
