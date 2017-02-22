//package uk.gov.ons.ras.collectioninstrument.dao;
//
//import com.google.gson.Gson;
//import org.postgresql.util.PGobject;
//import uk.gov.ons.ras.collectioninstrument.dao.CollectionInstrumentDao.CollectionInstrument;
//import javax.persistence.AttributeConverter;
//
//import javax.persistence.Converter;
//
//import java.io.IOException;
//
//@Converter(autoApply = true)
//public class JsonConverter implements AttributeConverter<CollectionInstrument, Object> {
//
//    private static final long serialVersionUID = 1L;
//
//    private Class<CollectionInstrument> clazz;
//
//    @Override
//    public Object convertToDatabaseColumn(CollectionInstrument json) {
//        try {
//            PGobject out = new PGobject();
//            out.setType("json");
//            out.setValue(new Gson().toJson(json));
//            return out;
//        } catch (Exception e) {
//            throw new IllegalArgumentException("Unable to serialize to json field ", e);
//        }
//    }
//
//    @Override
//    public CollectionInstrument convertToEntityAttribute(Object dataValue) {
//        if (dataValue instanceof PGobject && ((PGobject) dataValue).getType().equals("json"))
//            return new Gson().fromJson(((PGobject) dataValue).getValue(), CollectionInstrument.class);
//        return null;
//    }
//
//
//}